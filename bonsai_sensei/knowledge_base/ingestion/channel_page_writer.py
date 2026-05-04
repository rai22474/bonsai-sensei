import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_APP_NAME = "channel_page_writer"
_MAX_LLM_CALLS = 10

_WRITER_INSTRUCTION = """
Eres un redactor de wiki especializado en bonsái. Recibes una ficha de conocimiento extraída de un vídeo de expertos.

# Comportamiento
- Transforma la ficha en una página wiki en markdown bien estructurada
- Conserva toda la información técnica sin añadir ni inventar nada
- Usa un estilo enciclopédico, claro y directo
- Incluye siempre al final una sección ## Fuentes con el canal y la URL del vídeo original
- Guarda la página con save_wiki_page

# Formato
La página debe tener un título H1 descriptivo del tema principal, una introducción breve
y secciones organizadas por el contenido de la ficha (técnicas, especies, temporadas, consejos).
"""


def create_channel_page_writer(model: object) -> Callable[[Path, Path], Path]:
    """Create a writer that generates an official wiki page from a knowledge card.

    The page is saved under wiki/channels/{channel}/{video_id}.md and represents
    the crystallized knowledge of that video. Multiple channel pages can later be
    merged into topic pages through a separate human-reviewed process.

    Args:
        model: LLM model to use for the writer agent.

    Returns:
        Async callable: (card_path, wiki_root) -> page_path
    """
    async def write_channel_page(card_path: Path, wiki_root: Path) -> Path:
        card_content = card_path.read_text(encoding="utf-8")

        channel = card_path.parts[-2]
        video_id = card_path.stem
        page_path = wiki_root / "channels" / channel / f"{video_id}.md"

        if page_path.exists():
            logger.info("Channel wiki page already exists, skipping: %s", page_path)
            return page_path

        page_path.parent.mkdir(parents=True, exist_ok=True)

        def save_wiki_page(content: str) -> dict:
            """Save the wiki page to disk.

            Args:
                content: Full markdown content of the wiki page.

            Returns:
                {"status": "success"} on success.
            """
            page_path.write_text(content, encoding="utf-8")
            return {"status": "success"}

        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_WRITER_INSTRUCTION,
            tools=[save_wiki_page],
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id)

        prompt = f"Transforma esta ficha en una página wiki y guárdala con save_wiki_page:\n\n{card_content}"
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            pass

        logger.info("Channel wiki page saved: %s", page_path)
        return page_path

    return write_channel_page
