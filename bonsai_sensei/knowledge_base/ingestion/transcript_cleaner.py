import json
import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_APP_NAME = "transcript_cleaner"
_MAX_LLM_CALLS = 10

_CLEANER_INSTRUCTION = """
Eres un editor especializado en bonsái. Recibes una transcripción automática de YouTube con errores típicos: sin puntuación, fragmentos cortados, términos técnicos de bonsái posiblemente mal escritos.

# Comportamiento
- Une los fragmentos en párrafos coherentes respetando el flujo del discurso
- Añade puntuación y mayúsculas correctas
- Preserva nombres científicos, técnicas japonesas y terminología técnica de bonsái tal como se mencionan
- Elimina ruido: [Música], [Aplausos], fragmentos incomprensibles, repeticiones del subtitulado automático
- No añadas ni elimines información del contenido original
- Llama a save_clean_transcript con el resultado
"""


def create_transcript_cleaner(model: object) -> Callable[[Path, Path], Path]:
    """Create a cleaner that uses an LLM to produce a clean transcript from raw JSON.

    Args:
        model: LLM model to use for the cleaner agent.

    Returns:
        Async callable: (raw_path, transcripts_root) -> clean_path
    """
    async def clean_transcript(raw_path: Path, transcripts_root: Path) -> Path:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_text = " ".join(entry["text"] for entry in raw["entries"])

        clean_path = transcripts_root / "clean" / raw["channel"] / f"{raw['video_id']}.md"

        if clean_path.exists():
            logger.info("Clean transcript already exists, skipping: %s", clean_path)
            return clean_path

        clean_path.parent.mkdir(parents=True, exist_ok=True)

        def save_clean_transcript(text: str) -> dict:
            """Save the cleaned transcript text to disk.

            Args:
                text: Full cleaned transcript in plain text or markdown.

            Returns:
                {"status": "success"} on success.
            """
            clean_path.write_text(text, encoding="utf-8")
            return {"status": "success"}

        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_CLEANER_INSTRUCTION,
            tools=[save_clean_transcript],
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id)

        prompt = f"Limpia esta transcripción y guárdala con save_clean_transcript:\n\n{raw_text}"
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            pass

        logger.info("Clean transcript saved: %s", clean_path)
        return clean_path

    return clean_transcript
