import uuid
from pathlib import Path
from typing import Callable

from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.knowledge_base.keeper.agent import _APP_NAME, create_wiki_keeper_agent
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_MAX_LLM_CALLS = 40
_PROMPT = "Revisa todas las fichas de conocimiento y actualiza la wiki para que refleje todo el conocimiento disponible."


def create_wiki_keeper(model: object, transcripts_root: Path, wiki_root: Path) -> Callable[[], None]:
    """Create an autonomous wiki keeper that maintains coherence across all wiki pages.

    Triggered after each new video is ingested. Reads all knowledge cards from
    transcripts/cards/ and updates or creates topic pages in the main wiki autonomously.

    Args:
        model: LLM model to use.
        transcripts_root: Root directory for transcripts (cards are read from here).
        wiki_root: Root directory of the wiki.

    Returns:
        Async callable: () -> None
    """
    agent = create_wiki_keeper_agent(model, transcripts_root, wiki_root)

    async def run_wiki_keeper() -> None:
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id)

        message = types.Content(role="user", parts=[types.Part(text=_PROMPT)])
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            pass

        logger.info("Wiki keeper run completed")

    return run_wiki_keeper
