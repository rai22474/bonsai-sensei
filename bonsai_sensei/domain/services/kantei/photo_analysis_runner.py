import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

_APP_NAME = "photo_analysis"
_MAX_LLM_CALLS = 5

_ANALYSIS_INSTRUCTION = """
Eres el kantei de bonsáis, experto en evaluación visual de árboles.

Recibirás una foto de bonsái y una intención de análisis. Orienta tu respuesta a esa intención.
Cubre solo los aspectos relevantes para lo que se pide: si es salud, enfócate en signos de estrés,
plagas o carencias; si es diseño, en estructura, proporción, estilo y nebari; si es descripción general,
abarca agronómico y estético. Sé preciso y útil, no genérico.

Responde en castellano.
Usa HTML compatible con Telegram: <b>negrita</b>, <i>cursiva</i>, listas con • y saltos de línea.
No uses Markdown.
"""


def create_photo_analysis_runner(model: object) -> Callable:
    async def run_photo_analysis(photo_bytes: bytes, analysis_intent: str) -> str:
        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_ANALYSIS_INSTRUCTION,
        )
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME,
            user_id=_APP_NAME,
            session_id=session_id,
        )
        message = types.Content(
            role="user",
            parts=[
                types.Part(inline_data=types.Blob(mime_type="image/webp", data=photo_bytes)),
                types.Part(text=analysis_intent),
            ],
        )
        run_config = RunConfig(max_llm_calls=_MAX_LLM_CALLS)
        response_parts = []
        async for event in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=run_config,
        ):
            if event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_parts.append(part.text)
        return "\n".join(response_parts)

    return run_photo_analysis
