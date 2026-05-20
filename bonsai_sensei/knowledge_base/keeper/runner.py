import uuid
from pathlib import Path
from typing import Callable, Optional

from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types
from mem0 import AsyncMemory

from bonsai_sensei.knowledge_base.keeper.agent import _APP_NAME, create_wiki_keeper_agent
from bonsai_sensei.knowledge_base.keeper.memory_reader import read_new_observations, update_high_watermark
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_MAX_LLM_CALLS = 40
_BASE_PROMPT = (
    "Ejecuta las dos fases: "
    "1) enriquece la wiki con el conocimiento de las fichas; "
    "2) añade wikilinks en todas las páginas existentes donde falten."
)
_OBSERVATIONS_HEADER = (
    "\n\nAdemás, integra en la wiki las siguientes observaciones extraídas de conversaciones recientes con usuarios:\n"
)


def create_wiki_keeper(
    model: object,
    transcripts_root: Path,
    wiki_root: Path,
    mem0_client: Optional[AsyncMemory] = None,
) -> Callable[[], None]:
    """Create an autonomous wiki keeper that maintains coherence across all wiki pages.

    Triggered after each new video is ingested. Reads all knowledge cards from
    transcripts/cards/ and updates or creates topic pages in the main wiki autonomously.
    When mem0_client is provided, also integrates episodic observations from conversations.

    Args:
        model: LLM model to use.
        transcripts_root: Root directory for transcripts (cards are read from here).
        wiki_root: Root directory of the wiki.
        mem0_client: Optional mem0 async client for reading episodic observations.

    Returns:
        Async callable: () -> None
    """
    agent = create_wiki_keeper_agent(model, transcripts_root, wiki_root)

    async def run_wiki_keeper() -> None:
        prompt = await _build_prompt(mem0_client, wiki_root)

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

        if mem0_client is not None:
            update_high_watermark(wiki_root)

        logger.info("Wiki keeper run completed")

    return run_wiki_keeper


async def _build_prompt(mem0_client: Optional[AsyncMemory], wiki_root: Path) -> str:
    if mem0_client is None:
        return _BASE_PROMPT
    observations = await read_new_observations(mem0_client, wiki_root)
    if not observations:
        return _BASE_PROMPT
    observations_text = "\n".join(f"- {observation}" for observation in observations)
    logger.info("Wiki keeper found %d new episodic observations to process", len(observations))
    return _BASE_PROMPT + _OBSERVATIONS_HEADER + observations_text
