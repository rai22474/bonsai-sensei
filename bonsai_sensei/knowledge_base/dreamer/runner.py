import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types
from mem0 import AsyncMemory

from bonsai_sensei.knowledge_base.dreamer.agent import _APP_NAME, create_wiki_dreamer_agent
from bonsai_sensei.knowledge_base.dreamer.memory_reader import read_high_watermark, read_new_observations, update_high_watermark
from bonsai_sensei.knowledge_base import wiki_git
from bonsai_sensei.knowledge_base.wiki_index.indexer import update_page_index
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_MAX_LLM_CALLS = 100
_OBSERVATIONS_HEADER = (
    "Integra en la wiki las siguientes observaciones extraídas de conversaciones recientes con usuarios:\n"
)
_NEW_CARDS_HEADER = (
    "Enriquece la wiki con el conocimiento de las siguientes fichas nuevas:\n"
)
_WIKILINKS_PHASE = (
    "\n\nPor último, añade wikilinks en todas las páginas existentes donde falten."
)


def create_wiki_dreamer(
    model: object,
    transcripts_root: Path,
    wiki_root: Path,
    mem0_client: Optional[AsyncMemory] = None,
    notify_admin: Optional[Callable[[list[str], str], None]] = None,
    embed: Optional[Callable] = None,
) -> Callable[[], None]:
    """Create the wiki dreamer, an autonomous agent that maintains wiki coherence.

    Triggered after each new video is ingested. Reads all knowledge cards from
    transcripts/cards/ and updates or creates topic pages in the main wiki autonomously.
    When mem0_client is provided, also integrates episodic observations from conversations.
    When notify_admin is provided, sends a review notification after each run that changed pages.

    Args:
        model: LLM model to use.
        transcripts_root: Root directory for transcripts (cards are read from here).
        wiki_root: Root directory of the wiki.
        mem0_client: Optional mem0 async client for reading episodic observations.
        notify_admin: Optional async callable (changed_files, commit_hash) -> None.

    Returns:
        Async callable: () -> None
    """
    wiki_git.init_wiki_repo(wiki_root)
    agent = create_wiki_dreamer_agent(model, transcripts_root, wiki_root)

    async def run_wiki_dreamer() -> None:
        last_run = read_high_watermark(wiki_root)
        observations = await read_new_observations(mem0_client, wiki_root) if mem0_client is not None else []
        new_cards = _get_new_cards(transcripts_root, last_run)

        if not observations and not new_cards:
            logger.info("Wiki dreamer skipped: no new cards or observations since %s", last_run)
            return

        prompt = _build_prompt(observations, new_cards)
        logger.info("Wiki dreamer starting: %d new cards, %d new observations", len(new_cards), len(observations))
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id)

        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            pass

        update_high_watermark(wiki_root)

        commit_hash = wiki_git.commit_wiki_changes(wiki_root, "dreamer: update wiki pages")
        if commit_hash:
            changed_files = wiki_git.get_changed_files(wiki_root, commit_hash)
            if changed_files and embed is not None:
                for file_path in changed_files:
                    if file_path.endswith(".md"):
                        await update_page_index(file_path, wiki_root, embed)
            if changed_files and notify_admin:
                await notify_admin(changed_files, commit_hash)

        logger.info("Wiki dreamer run completed")

    return run_wiki_dreamer


def _get_new_cards(transcripts_root: Path, since: datetime) -> list[str]:
    cards_root = transcripts_root / "cards"
    if not cards_root.exists():
        return []
    return sorted(
        str(card.relative_to(cards_root))
        for card in cards_root.rglob("*.md")
        if datetime.fromtimestamp(card.stat().st_mtime, tz=timezone.utc) > since
    )


def _build_prompt(observations: list[str], new_cards: list[str]) -> str:
    parts = []
    if observations:
        observations_text = "\n".join(f"- {observation}" for observation in observations)
        parts.append(_OBSERVATIONS_HEADER + observations_text)
    if new_cards:
        cards_text = "\n".join(f"- {card}" for card in new_cards)
        parts.append(_NEW_CARDS_HEADER + cards_text)
    parts.append(_WIKILINKS_PHASE.strip())
    return "\n\n".join(parts)
