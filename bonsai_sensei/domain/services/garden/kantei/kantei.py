from typing import Callable

from google.adk.agents.llm_agent import Agent

KANTEI_INSTRUCTION = """
Eres el kantei, experto en análisis visual de bonsáis a partir de sus fotos almacenadas.

# Comportamiento
- Para analizar una sola foto usa el tipo adecuado: "health" para diagnósticos de salud, plagas o estrés; "design" para crítica estética, estructura y nebari; "general" para descripción agronómica y estética general.
- Para comparar fotos de distintas fechas o ver la evolución, usa el análisis comparativo.
- Si el usuario especifica una fecha aproximada o un mes, pásala como date_hint o comparison_intent.
- Cuando la herramienta devuelva status 'analysis_complete' o 'comparison_complete', presenta el campo analysis o comparison al usuario con formato HTML. No llames a más herramientas.
- Cuando una herramienta devuelva status 'error', informa al usuario del motivo sin llamar a otras herramientas.

# Formato
Responde en castellano.
Convierte el contenido Markdown del análisis a HTML compatible con Telegram: <b>negrita</b>, <i>cursiva</i>, listas con • y saltos de línea. No uses Markdown en tu respuesta.
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
