import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events

_APP_NAME = "photo_analysis"
_MAX_LLM_CALLS = 8

_ANALYSIS_INSTRUCTION = """
Eres el kantei de bonsáis, experto en evaluación visual de árboles.
Sé preciso y útil, no genérico. Responde en castellano.
Usa Markdown: **negrita**, *cursiva*, listas con - y saltos de línea.

Para análisis de salud (health): si identificas una plaga, enfermedad o síntoma específico,
búscalo en la wiki con search_wiki_knowledge antes de dar recomendaciones de tratamiento.
Ejemplo: si ves síntomas de ácaros, busca "ácaros enfermedad tratamiento".
"""

_PROMPTS = {
    "health": (
        "Analiza la salud de este bonsái. Identifica signos de estrés hídrico, carencias nutricionales, "
        "plagas o enfermedades visibles. Incluye al menos una recomendación accionable."
    ),
    "design": (
        "Critica el diseño estético de este bonsái. Evalúa línea de tronco, nebari, distribución de ramas, "
        "proporción, movimiento y coherencia de estilo. Señala los puntos más importantes a mejorar."
    ),
    "general": (
        "Describe el estado general de este bonsái: aspecto agronómico (vigor, follaje, salud visible) "
        "y aspecto estético (forma, estructura, equilibrio visual)."
    ),
}


def create_photo_analysis_runner(model: object, search_wiki_knowledge: Callable | None = None) -> Callable:
    tools = [search_wiki_knowledge] if search_wiki_knowledge is not None else []

    async def run_photo_analysis(photo_bytes: bytes, analysis_type: str) -> str:
        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_ANALYSIS_INSTRUCTION,
            tools=tools,
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
                types.Part(text=_PROMPTS[analysis_type]),
            ],
        )
        return await extract_text_from_events(runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ))

    return run_photo_analysis
