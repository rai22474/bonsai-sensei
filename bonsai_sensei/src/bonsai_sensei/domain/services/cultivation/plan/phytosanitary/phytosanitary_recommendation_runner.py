import json
from typing import Callable

from google.genai import types

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events
from bonsai_sensei.domain.services.llm_runner import create_single_turn_llm_runner

_APP_NAME = "phytosanitary_recommendation"
_MAX_LLM_CALLS = 3

_INSTRUCTION = """
Eres un experto en fitosanidad de bonsáis.
Analiza el contexto proporcionado — historial de eventos, plan existente, catálogo y fichas técnicas — y diseña un plan de protección completo y equilibrado.

Ten en cuenta:
- La estación actual (derivada de la fecha) determina las amenazas prevalentes: primavera/verano = alta actividad de ácaros, pulgones y cochinillas; otoño/invierno = riesgo fúngico por humedad y frío.
- Si el historial muestra una plaga o enfermedad activa, prioriza el tratamiento curativo adecuado.
- Si no hay incidencias recientes, diseña un plan preventivo estacional.
- Rota entre productos de diferente mecanismo de acción para evitar resistencias.
- Si el bonsái está estresado, en recuperación o recién trasplantado, reduce la intensidad de los tratamientos.

Devuelve ÚNICAMENTE un JSON válido con este formato exacto, sin texto adicional:
{
  "treatments": [
    {
      "phytosanitary_name": "<nombre exacto del producto tal como aparece en el catálogo>",
      "purpose": "<objetivo del tratamiento: qué plaga o enfermedad combate o previene>"
    }
  ],
  "reasoning": "<justificación del plan completo en 3-5 oraciones>",
  "wiki_content": "<contenido completo en markdown para la página de plan fitosanitario>"
}

Incluye tantos tratamientos como el historial, las fichas técnicas y el catálogo disponible justifiquen. No añadas tratamientos sin fundamento ni omitas los que el contexto requiera.

El wiki_content debe seguir esta estructura:
# Plan fitosanitario

## Plan activo
[tabla o lista con cada tratamiento: producto, objetivo, dosis, frecuencia]
[razonamiento del plan]

## Historial
[planes anteriores del historial existente, íntegros; si no hay historial previo, dejar la sección vacía]
"""


def create_phytosanitary_recommendation_runner(model: object) -> Callable:
    run_llm = create_single_turn_llm_runner(
        model=model,
        app_name=_APP_NAME,
        instruction=_INSTRUCTION,
        max_llm_calls=_MAX_LLM_CALLS,
    )

    async def run_phytosanitary_recommendation(context: str) -> dict:
        message = types.Content(role="user", parts=[types.Part(text=context)])
        raw = await extract_text_from_events(run_llm(message))
        return json.loads(raw)

    return run_phytosanitary_recommendation
