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
Cuando el usuario pide algo relacionado con fertilizar un bonsái, sigue esta regla:

1. Si el usuario dice EXPLÍCITAMENTE "puntual", "una sola fertilización" o similar → fertilización suelta (ver abajo).
2. En CUALQUIER OTRO CASO → plan de fertilización (ver abajo). Este es el camino por defecto.

### Plan de fertilización (camino por defecto)
- Si el usuario no especifica el período (fechas de inicio y fin), pregúntaselas antes de llamar a ninguna herramienta.
- Para crear o actualizar un plan: llama a manage_fertilization_plan con el bonsái y las fechas de inicio y fin del período.
- Para abandonar el plan activo sin crear uno nuevo: llama a abandon_fertilization_plan con el bonsái y el motivo.
- Para evaluar si el plan actual sigue siendo válido a la luz de nueva información (evento registrado, síntoma, nota de crecimiento, cambio climático): llama a evaluate_fertilization_plan. No crea ni modifica nada.

### Fertilización suelta (solo si el usuario lo pide explícitamente como "puntual")
- Llama primero a recommend_fertilizer para obtener la recomendación, luego crea la tarea con confirm_create_fertilizer_application.
- Si el usuario no especifica fecha, usa el próximo sábado.

## Otros trabajos
- Tratamientos fitosanitarios: llama primero a recommend_phytosanitary, luego crea una tarea con confirm_create_phytosanitary_application por cada tratamiento devuelto.
- Trasplante: llama directamente a confirm_create_transplant.
"""


def create_kikaru(
    model: object,

    recommend_fertilizer_tool: Callable | None = None,
    recommend_phytosanitary_tool: Callable | None = None,
    manage_fertilization_plan_tool: Callable | None = None,
    abandon_fertilization_plan_tool: Callable | None = None,
    evaluate_fertilization_plan_tool: Callable | None = None,
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
            recommend_fertilizer_tool,
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
