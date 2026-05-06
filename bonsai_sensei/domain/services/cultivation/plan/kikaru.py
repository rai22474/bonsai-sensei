from typing import Callable

from google.adk.agents.llm_agent import LlmAgent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call

KIKARU_INSTRUCTION = """
Eres el responsable de la planificación de trabajos de cultivo de bonsáis.
Gestionas el calendario de fertilizaciones, tratamientos fitosanitarios y trasplantes.

# Contexto
Fecha de hoy: {current_date}
Próximo sábado: {next_saturday}

# Comportamiento
- Si el usuario NO especifica fecha, usa el próximo sábado por defecto.
- Para planificar una fertilización: llama primero a recommend_fertilizer para obtener la recomendación y el racional, luego usa el fertilizante devuelto para crear la tarea con confirm_create_fertilizer_application.
- Para planificar tratamientos fitosanitarios: llama primero a recommend_phytosanitary para obtener el plan completo. Luego crea una tarea con confirm_create_phytosanitary_application por cada tratamiento de la lista "treatments" devuelta.
- Para planificar un trasplante: llama directamente a confirm_create_transplant.
- Si falta el nombre del bonsái, pídelo antes de llamar a ninguna herramienta.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
"""


def create_kikaru(
    model: object,

    recommend_fertilizer_tool: Callable | None = None,
    recommend_phytosanitary_tool: Callable | None = None,
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
