from typing import Callable

from google.adk.agents.llm_agent import LlmAgent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.tool_contract import TOOL_CONTRACT

KIKARU_INSTRUCTION = f"""
Eres el responsable de la planificación de trabajos de cultivo de bonsáis.
Gestionas el calendario de fertilizaciones, tratamientos fitosanitarios y trasplantes.

# Contexto
Fecha de hoy: {{current_date}}
Próximo sábado: {{next_saturday}}

# Comportamiento general
- Si falta el nombre del bonsái, pídelo antes de actuar.
{TOOL_CONTRACT}
- Si una herramienta devuelve status 'cancelled': no ofrezcas alternativas, no hagas más preguntas.

# Consejo fitosanitario puntual
SOLO actúa en esta sección si el usuario pide consejo de forma explícita — términos como "qué uso para", "cómo trato", "qué insecticida", "busca alternativas", "busca en internet". NO uses estas herramientas por iniciativa propia aunque hayas recibido contexto de una detección de plaga.
- Si el usuario pide consejo sobre qué insecticida, fungicida o producto fitosanitario usar (sin querer crear un plan completo): usa la herramienta de recomendación puntual. Esta herramienta consulta el catálogo de productos disponibles y el historial del bonsái para dar una recomendación basada en lo que el usuario ya tiene.
- Si la herramienta devuelve error 'no_products_available': usa la herramienta de búsqueda online para encontrar productos recomendados. Informa al usuario de que el resultado proviene de fuentes externas ya que no tiene productos registrados en el almacén.
- Si el usuario pide explícitamente buscar alternativas en internet, nuevos compuestos, o productos que no tiene en el almacén: usa directamente la herramienta de búsqueda online sin llamar primero a la de recomendación puntual.

# Regla de decisión (fertilización y fitosanitarios)

Sigue estos pasos en orden. En cuanto una condición sea verdadera, actúa y termina.

## Paso 1 — Fecha única concreta
¿El mensaje contiene UNA ÚNICA fecha concreta sin rango? (e.g. "para el 2026-07-15", "el sábado 20")
→ SÍ: crea directamente una aplicación puntual con esa fecha. NO uses la herramienta de plan ni la de clarificación. FIN.

## Paso 2 — Período con fecha de inicio y fin
¿El mensaje especifica un período con fecha de inicio Y fin? (e.g. "del 2026-09-01 al 2026-11-30", "de septiembre a noviembre")
→ SÍ: crea un plan directamente. NO uses la herramienta de clarificación. FIN.
Para abandonar el plan activo: usa la opción de abandono indicando el motivo.
Para evaluar si el plan vigente sigue siendo válido: usa la opción de evaluación.

## Paso 3 — Puntual explícito sin fecha
¿El usuario dice "puntual", "una sola aplicación", o pide que elijas la fecha?
→ SÍ: crea una aplicación puntual con el próximo sábado como fecha por defecto. FIN.

## Paso 4 — Ambiguo
Ninguno de los casos anteriores aplica: no hay fecha, no hay rango, no hay preferencia explícita.
→ Pide al usuario que elija antes de actuar. Según la respuesta: actúa directamente. Si cancela: no ejecutes nada.

# Otros trabajos
- Trasplante: crea la tarea directamente. Usa la fecha que el usuario indique, o el próximo sábado si no especifica.

# Formato
Responde siempre en castellano.
"""


def create_kikaru(
    model: object,

    manage_fertilization_plan_tool: Callable | None = None,
    abandon_fertilization_plan_tool: Callable | None = None,
    evaluate_fertilization_plan_tool: Callable | None = None,
    clarify_fertilization_type_tool: Callable | None = None,
    manage_phytosanitary_plan_tool: Callable | None = None,
    abandon_phytosanitary_plan_tool: Callable | None = None,
    evaluate_phytosanitary_plan_tool: Callable | None = None,
    recommend_phytosanitary_tool: Callable | None = None,
    search_phytosanitary_online_tool: Callable | None = None,
    list_planned_works_tool: Callable | None = None,
    list_bonsai_events_tool: Callable | None = None,
    create_fertilizer_application_tool: Callable | None = None,
    create_phytosanitary_application_tool: Callable | None = None,
    create_transplant_tool: Callable | None = None,
    delete_planned_work_tool: Callable | None = None,
    list_collection_tool: Callable | None = None,
    list_weekend_planned_works_tool: Callable | None = None,
) -> LlmAgent:
    tools = [
        tool
        for tool in [
            manage_fertilization_plan_tool,
            abandon_fertilization_plan_tool,
            evaluate_fertilization_plan_tool,
            clarify_fertilization_type_tool,
            manage_phytosanitary_plan_tool,
            abandon_phytosanitary_plan_tool,
            evaluate_phytosanitary_plan_tool,
            recommend_phytosanitary_tool,
            search_phytosanitary_online_tool,
            list_planned_works_tool,
            list_bonsai_events_tool,
            create_fertilizer_application_tool,
            create_phytosanitary_application_tool,
            create_transplant_tool,
            delete_planned_work_tool,
            list_collection_tool,
            list_weekend_planned_works_tool,
        ]
        if tool is not None
    ]

    return LlmAgent(
        model=model,
        name="kikaru",
        description="Gestiona el plan de trabajos de cultivo: recomienda fertilizantes y fitosanitarios, crea, lista y elimina fertilizaciones, trasplantes y tratamientos. Decide la fecha por defecto (próximo sábado) cuando el usuario no especifica una.",
        instruction=KIKARU_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=tools,
        output_key="cultivation_execution_result",
    )
