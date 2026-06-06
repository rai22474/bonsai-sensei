import functools
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Optional

from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types
from jinja2 import Environment, FileSystemLoader
from knowledge_base.dreamer.memory_reader import (
    read_admin_corrections,
    read_high_watermark,
    read_local_observations,
    read_new_observations,
    update_high_watermark,
)
from knowledge_base import wiki_git
from knowledge_base.wiki_index.indexer import update_page_index
from knowledge_base.logging_config import get_logger
from knowledge_base.metrics import DREAMER_RUNS_TOTAL, DREAMER_PAGES_CHANGED_TOTAL

logger = get_logger(__name__)

_MAX_LLM_CALLS_OBSERVATIONS = 20
_MAX_LLM_CALLS_CARDS = 60
_MAX_LLM_CALLS_WIKILINKS = 50
_WIKILINKS_BATCH_SIZE = 5
_PROCESSED_WIKILINKS_FILE = "dreamer-processed-wikilinks.json"

_prompt_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def create_wiki_dreamer(
    observations_agent: Agent,
    cards_agent: Agent,
    wikilinks_agent: Agent,
    wiki_root: Path,
    transcripts_root: Path,
    notify_admin: Optional[Callable[[list[str], str], None]] = None,
    embed: Optional[Callable] = None,
    save_entry: Optional[Callable] = None,
    episodic_memory_url: str = "",
) -> Callable[[], None]:
    """Assemble agents and I/O dependencies into a zero-argument callable that runs the wiki dreamer.

    Acts as a composition root: resolves raw config (paths, URLs) into callables and binds
    them into run_wiki_dreamer via partial application.

    Args:
        observations_agent: Agent that integrates conversation observations.
        cards_agent: Agent that enriches the wiki from knowledge cards.
        wikilinks_agent: Agent that adds wikilinks to knowledge pages.
        wiki_root: Root directory of the wiki.
        transcripts_root: Root directory for transcripts (cards are read from here).
        notify_admin: Optional async callable (changed_files, commit_hash) -> None.

    Returns:
        Async callable: () -> None
    """
    wiki_git.init_wiki_repo(wiki_root)

    async def read_observations() -> list[str]:
        return (
            (await read_new_observations(episodic_memory_url, wiki_root) if episodic_memory_url else [])
            + read_local_observations(wiki_root)
            + read_admin_corrections(wiki_root)
        )

    def save_run_state(wikilinks_batch: list[str]) -> None:
        update_high_watermark(wiki_root)
        if wikilinks_batch:
            _mark_wikilinks_processed(wiki_root, wikilinks_batch)

    return functools.partial(
        run_wiki_dreamer,
        read_observations,
        functools.partial(_get_new_cards, transcripts_root),
        functools.partial(_get_wikilinks_batch, wiki_root, _WIKILINKS_BATCH_SIZE),
        functools.partial(read_high_watermark, wiki_root),
        functools.partial(_integrate_observations, observations_agent),
        functools.partial(_enrich_from_knowledge_cards, cards_agent),
        functools.partial(_add_wikilinks, wikilinks_agent),
        save_run_state,
        functools.partial(_commit_index_and_notify, wiki_root, embed, save_entry, notify_admin),
    )


async def run_wiki_dreamer(
    read_observations: Callable[[], Awaitable[list[str]]],
    read_new_cards: Callable[[datetime], list[str]],
    read_wikilinks_batch: Callable[[], list[str]],
    read_last_run: Callable[[], datetime],
    integrate_observations: Callable[[list[str]], Awaitable[None]],
    enrich_from_knowledge_cards: Callable[[list[str]], Awaitable[None]],
    add_wikilinks: Callable[[list[str]], Awaitable[None]],
    save_run_state: Callable[[list[str]], None],
    commit_and_notify: Callable[[], Awaitable[None]],
) -> None:
    last_run = read_last_run()
    observations = await read_observations()
    new_cards = read_new_cards(last_run)
    wikilinks_batch = read_wikilinks_batch()

    if not observations and not new_cards and not wikilinks_batch:
        logger.info("Wiki dreamer skipped: no new cards, observations, or pending wikilinks since %s", last_run)
        DREAMER_RUNS_TOTAL.labels(outcome="no_changes").inc()
        return

    logger.info(
        "Wiki dreamer starting: %d new cards, %d new observations, %d wikilink pages",
        len(new_cards), len(observations), len(wikilinks_batch),
    )

    await integrate_observations(observations)
    await enrich_from_knowledge_cards(new_cards)
    await add_wikilinks(wikilinks_batch)

    save_run_state(wikilinks_batch)
    await commit_and_notify()
    logger.info("Wiki dreamer run completed")


async def _commit_index_and_notify(
    wiki_root: Path,
    embed: Optional[Callable],
    save_entry: Optional[Callable],
    notify_admin: Optional[Callable[[list[str], str], None]],
) -> None:
    commit_hash = wiki_git.commit_wiki_changes(wiki_root, "dreamer: update wiki pages")
    if commit_hash:
        changed_files = wiki_git.get_changed_files(wiki_root, commit_hash)
        if changed_files and embed is not None:
            for file_path in changed_files:
                if file_path.endswith(".md"):
                    await update_page_index(file_path, wiki_root, embed, save_entry)
        
        if changed_files:
            DREAMER_RUNS_TOTAL.labels(outcome="changed").inc()
            DREAMER_PAGES_CHANGED_TOTAL.inc(len(changed_files))
            if notify_admin:
                await notify_admin(changed_files, commit_hash)
    else:
        DREAMER_RUNS_TOTAL.labels(outcome="no_changes").inc()


async def _integrate_observations(agent: Agent, observations: list[str]) -> None:
    if not observations:
        return
    
    prompt = _prompt_env.get_template("observations_prompt.jinja2").render(observations=observations).strip()
    await _run_phase(agent, prompt, _MAX_LLM_CALLS_OBSERVATIONS, "integrate observations")


async def _enrich_from_knowledge_cards(agent: Agent, new_cards: list[str]) -> None:
    if not new_cards:
        return
    
    prompt = _prompt_env.get_template("cards_prompt.jinja2").render(new_cards=new_cards).strip()
    await _run_phase(agent, prompt, _MAX_LLM_CALLS_CARDS, "enrich from knowledge cards")


async def _add_wikilinks(agent: Agent, wikilinks_batch: list[str]) -> None:
    if not wikilinks_batch:
        return
    
    prompt = _prompt_env.get_template("wikilinks_prompt.jinja2").render(wikilinks_batch=wikilinks_batch).strip()
    await _run_phase(agent, prompt, _MAX_LLM_CALLS_WIKILINKS, "add wikilinks")


async def _run_phase(agent: Agent, prompt: str, max_llm_calls: int, phase_name: str) -> None:
    logger.info("Wiki dreamer phase starting: %s", phase_name)
    runner = InMemoryRunner(agent=agent, app_name=agent.name)
    session_id = str(uuid.uuid4())
    await runner.session_service.create_session(app_name=agent.name, user_id=agent.name, session_id=session_id)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    try:
        async for _ in runner.run_async(
            user_id=agent.name,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=max_llm_calls),
        ):
            pass
    except LlmCallsLimitExceededError:
        logger.warning("Wiki dreamer phase hit LLM calls limit, partial progress kept: %s (limit=%d)", phase_name, max_llm_calls)
    logger.info("Wiki dreamer phase completed: %s", phase_name)


def _get_new_cards(transcripts_root: Path, since: datetime) -> list[str]:
    cards_root = transcripts_root / "cards"
    if not cards_root.exists():
        return []
    return sorted(
        str(card.relative_to(cards_root))
        for card in cards_root.rglob("*.md")
        if datetime.fromtimestamp(card.stat().st_mtime, tz=timezone.utc) >= since
    )


def _get_wikilinks_batch(wiki_root: Path, batch_size: int) -> list[str]:
    processed = _read_processed_wikilinks(wiki_root)
    pending = []
    for page in wiki_root.rglob("*.md"):
        rel = str(page.relative_to(wiki_root))
        if rel.startswith(("bonsai/", "wiki-index/")):
            continue
        mtime = page.stat().st_mtime
        if processed.get(rel) != mtime:
            pending.append(rel)
    return sorted(pending)[:batch_size]


def _read_processed_wikilinks(wiki_root: Path) -> dict[str, float]:
    wikilinks_file = wiki_root / _PROCESSED_WIKILINKS_FILE
    if not wikilinks_file.exists():
        return {}
    return json.loads(wikilinks_file.read_text())


def _mark_wikilinks_processed(wiki_root: Path, pages: list[str]) -> None:
    processed = _read_processed_wikilinks(wiki_root)
    for rel in pages:
        page = wiki_root / rel
        if page.exists():
            processed[rel] = page.stat().st_mtime
    wikilinks_file = wiki_root / _PROCESSED_WIKILINKS_FILE
    wikilinks_file.write_text(json.dumps(processed))
