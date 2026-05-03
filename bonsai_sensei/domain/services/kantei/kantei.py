from typing import Callable

from google.adk.agents.llm_agent import Agent

KANTEI_INSTRUCTION = """
Eres el kantei, experto en análisis visual de bonsáis a partir de sus fotos almacenadas.

# Comportamiento
- Para analizar, describir, diagnosticar o criticar una sola foto: llama siempre a analyze_bonsai_photo. Nunca respondas sin haber obtenido primero el resultado de la herramienta.
- Para comparar fotos de distintas fechas o ver la evolución de un bonsái: llama siempre a compare_bonsai_photos.
- Si el usuario especifica una fecha aproximada o un mes, pásala tal cual como date_hint o comparison_intent.
"""


def create_kantei(
    model: object,
    analyze_bonsai_photo_tool: Callable,
    compare_bonsai_photos_tool: Callable,
) -> Agent:
    return Agent(
        model=model,
        name="kantei",
        description="Evalúa visualmente fotos almacenadas de bonsáis: describe su estado agronómico y estético, diagnostica problemas, critica el diseño y compara fotos de distintas fechas para ver la evolución.",
        instruction=KANTEI_INSTRUCTION,
        tools=[analyze_bonsai_photo_tool, compare_bonsai_photos_tool],
    )
