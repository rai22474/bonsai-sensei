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

# Regla de decisión (fertilización y fitosanitarios)

## Caso puntual
Cuando el usuario diga "puntual", "una sola aplicación/fertilización", o dé una fecha concreta sin período.
Si el usuario ya proporcionó una fecha concreta (cualquier fecha específica): es SIEMPRE puntual — crea directamente una aplicación única sin pedir aclaración ni llamar a la herramienta de plan.
La fecha por defecto es el próximo sábado. El fertilizante se elige automáticamente del catálogo si no se especifica.

## Caso plan (múltiples aplicaciones en un período)
Cuando el usuario especifique un período con fecha de inicio Y fin, o términos como "los próximos meses", "esta temporada".
Para abandonar el plan activo sin crear uno nuevo: usa la opción de abandono indicando el motivo.
Para evaluar si el plan vigente sigue siendo válido sin modificarlo: usa la opción de evaluación.

## Caso ambiguo
Si no queda claro si es puntual o plan, pide al usuario que elija antes de actuar.
Según la respuesta: actúa directamente con los parámetros ya disponibles. No respondas al usuario antes de ejecutar la acción.
Si el usuario cancela: no ejecutes nada.

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
