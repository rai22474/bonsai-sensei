import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_APP_NAME = "card_extractor"
_MAX_LLM_CALLS = 10

_EXTRACTOR_INSTRUCTION = """
Eres un extractor de conocimiento especializado en bonsái. Recibes la transcripción limpia de un vídeo de un experto.

# Comportamiento
- Identifica y extrae el conocimiento técnico concreto: especies, técnicas, épocas, consejos de cuidado
- Descarta anécdotas, saludos, agradecimientos y contenido sin valor técnico
- Sé fiel al contenido original: no inventes ni interpretes más allá de lo que el experto dice
- Estructura la ficha en el formato indicado y guárdala con save_knowledge_card

# Formato de la ficha
La ficha debe seguir esta estructura exacta:

  # Ficha: <título o descripción del vídeo>

  ## Fuente
  - Canal: <nombre del canal>
  - URL: <url del vídeo>

  ## Especies mencionadas
  - <especie>: contexto breve de qué se dice sobre ella

  ## Técnicas
  ### <nombre de la técnica>
  <descripción de cómo y cuándo aplicarla según el experto>

  ## Temporadas y épocas
  - <estación>: <qué hacer o qué evitar>

  ## Consejos destacados
  - <consejo concreto y accionable>

Omite secciones que no tengan contenido relevante en el vídeo.
"""


def create_card_extractor(model: object) -> Callable[[Path, Path], Path]:
    """Create an extractor that uses an LLM to produce a structured knowledge card from a clean transcript.

    Args:
        model: LLM model to use for the extractor agent.

    Returns:
        Async callable: (clean_path, transcripts_root) -> card_path
    """
    async def extract_card(clean_path: Path, transcripts_root: Path) -> Path:
        clean_text = clean_path.read_text(encoding="utf-8")

        parts = clean_path.parts
        channel = parts[-2]
        video_id = clean_path.stem

        card_path = transcripts_root / "cards" / channel / f"{video_id}.md"

        if card_path.exists():
            logger.info("Knowledge card already exists, skipping: %s", card_path)
            return card_path

        card_path.parent.mkdir(parents=True, exist_ok=True)

        def save_knowledge_card(content: str) -> dict:
            """Save the structured knowledge card to disk.

            Args:
                content: Full markdown content of the knowledge card.

            Returns:
                {"status": "success"} on success.
            """
            card_path.write_text(content, encoding="utf-8")
            return {"status": "success"}

        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_EXTRACTOR_INSTRUCTION,
            tools=[save_knowledge_card],
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id)

        prompt = f"Extrae la ficha de conocimiento de esta transcripción y guárdala con save_knowledge_card:\n\n{clean_text}"
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            pass

        logger.info("Knowledge card saved: %s", card_path)
        return card_path

    return extract_card
