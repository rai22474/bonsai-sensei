from typing import Callable

from google.adk.agents.llm_agent import LlmAgent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call

KIKARU_INSTRUCTION = """
Eres el responsable de la planificación de trabajos de cultivo de bonsáis.
Gestionas el calendario de fertilizaciones, tratamientos fitosanitarios y trasplantes.

Responde siempre en castellano.

# Contexto
Fecha de hoy: {current_date}
Próximo sábado: {next_saturday}

# Comportamiento general
- Si falta el nombre del bonsái, pídelo antes de llamar a ninguna herramienta.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.

## Fertilización — regla de decisión

### Fertilización puntual (UNA sola aplicación)
Úsala cuando el usuario diga "puntual", "una sola fertilización", o dé una única fecha concreta sin período.
El fertilizante se elige automáticamente del catálogo si el usuario no lo especifica. La fecha por defecto es el próximo sábado.

### Plan de fertilización (múltiples aplicaciones en un período)
Úsalo cuando el usuario especifique un período con fecha de inicio Y fin, o términos como "los próximos meses", "esta temporada".
Para abandonar el plan activo sin crear uno nuevo: usa la función de abandono con el motivo.
Para evaluar si el plan actual sigue siendo válido a la luz de nueva información: usa la función de evaluación (no crea ni modifica nada).

### Caso ambiguo
Si no queda claro si el usuario quiere una fertilización puntual o un plan para un período, pídele que elija antes de actuar.

## Otros trabajos
- Tratamientos fitosanitarios: obtén primero la recomendación fitosanitaria y luego crea una tarea por cada tratamiento devuelto.
- Trasplante: crea la tarea directamente.
"""


def create_kikaru(
    model: object,

    recommend_phytosanitary_tool: Callable | None = None,
    manage_fertilization_plan_tool: Callable | None = None,
    abandon_fertilization_plan_tool: Callable | None = None,
    evaluate_fertilization_plan_tool: Callable | None = None,
    clarify_fertilization_type_tool: Callable | None = None,
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
            recommend_phytosanitary_tool,
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
