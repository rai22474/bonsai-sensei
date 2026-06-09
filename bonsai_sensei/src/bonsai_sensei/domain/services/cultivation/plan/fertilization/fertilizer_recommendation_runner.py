import json
import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events

_APP_NAME = "fertilizer_recommendation"
_MAX_LLM_CALLS = 3

_INSTRUCTION = """
Eres un experto en fertilización de bonsáis.
Analiza el contexto proporcionado — historial de eventos, plan existente, catálogo y fichas técnicas — y diseña un plan de fertilización estacional completo.

Ten en cuenta:
- La estación actual (derivada de la fecha) determina las necesidades: primavera = nitrógeno alto para crecimiento, verano = equilibrado, otoño = potasio para endurecimiento, invierno = pausa o mínima fertilización.
- Si el historial muestra signos de estrés, enfermedad activa o tratamientos fitosanitarios recientes, ajusta el plan: reduce dosis o frecuencia hasta que el bonsái se recupere.
- Rota entre fertilizantes orgánicos e inorgánicos si el catálogo lo permite.

Devuelve ÚNICAMENTE un JSON válido con este formato exacto, sin texto adicional:
{
  "fertilizer_name": "<nombre exacto del fertilizante recomendado para aplicar AHORA, tal como aparece en el catálogo>",
  "reasoning": "<justificación de la elección actual en 2-4 oraciones>",
  "wiki_content": "<contenido completo en markdown para la página de plan de fertilización>"
}

El wiki_content debe seguir esta estructura:
# Plan de fertilización

## Plan activo
[plan estacional completo: qué aplicar en cada estación, dosis y frecuencia]
[ajustes por salud si aplican]

## Historial
[planes anteriores del historial existente, íntegros; si no hay historial previo, dejar la sección vacía]
"""


def create_fertilizer_recommendation_runner(model: object) -> Callable:
    async def run_fertilizer_recommendation(context: str) -> dict:
        agent = Agent(
            model=model,
            name=_APP_NAME,
            instruction=_INSTRUCTION,
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
            parts=[types.Part(text=context)],
        )
        raw = await extract_text_from_events(runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ))
        return json.loads(raw)

    return run_fertilizer_recommendation
