from typing import Callable

from google.adk.agents.llm_agent import LlmAgent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.tool_contract import TOOL_CONTRACT

KIKARU_INSTRUCTION = f"""
Eres kikaru, el agente de planificación de cultivo. Gestionas el calendario de fertilizaciones, tratamientos fitosanitarios, planes de desarrollo artístico y trasplantes de bonsáis.

# Contexto
Fecha de hoy: {{current_date}}
Próximo sábado: {{next_saturday}}

# Comportamiento
- Actúa directamente con los parámetros que el usuario indique; no preguntes antes — las herramientas gestionan lo que falte internamente.
- Usa el próximo sábado como fecha por defecto cuando el usuario no especifique una.
- Para eliminar un trabajo planificado: lista primero los trabajos del bonsái para obtener el ID, luego elimínalo.
- Los tratamientos fitosanitarios solo entran aquí cuando el usuario quiere programar uno con fecha. Las peticiones de consejo o recomendación no son tuyas.
- Cuando el usuario quiera abrir una sesión de documentación de un trabajo planificado — preparar cómo ejecutarlo (análisis previo) o registrar lo que hizo tras terminarlo (resultado) — inicia la documentación del trabajo. Esto transfiere el canal al agente de documentación.
{TOOL_CONTRACT}
- Si una herramienta devuelve status 'cancelled': no ofrezcas alternativas ni hagas más preguntas.

# Formato
Responde en castellano.
"""


def create_kikaru(
    model: object,
    schedule_fertilization_tool: Callable | None = None,
    abandon_fertilization_plan_tool: Callable | None = None,
    evaluate_fertilization_plan_tool: Callable | None = None,
    schedule_phytosanitary_tool: Callable | None = None,
    abandon_phytosanitary_plan_tool: Callable | None = None,
    evaluate_phytosanitary_plan_tool: Callable | None = None,
    manage_development_plan_tool: Callable | None = None,
    abandon_development_plan_tool: Callable | None = None,
    evaluate_development_plan_tool: Callable | None = None,
    create_transplant_tool: Callable | None = None,
    delete_planned_work_tool: Callable | None = None,
    list_planned_works_tool: Callable | None = None,
    start_work_documentation_tool: Callable | None = None,
) -> LlmAgent:
    tools = [
        tool
        for tool in [
            schedule_fertilization_tool,
            abandon_fertilization_plan_tool,
            evaluate_fertilization_plan_tool,
            schedule_phytosanitary_tool,
            abandon_phytosanitary_plan_tool,
            evaluate_phytosanitary_plan_tool,
            manage_development_plan_tool,
            abandon_development_plan_tool,
            evaluate_development_plan_tool,
            create_transplant_tool,
            delete_planned_work_tool,
            list_planned_works_tool,
            start_work_documentation_tool,
        ]
        if tool is not None
    ]

    return LlmAgent(
        model=model,
        name="kikaru",
        description="Programa fertilizaciones y tratamientos fitosanitarios (puntuales o por período), gestiona planes de desarrollo artístico del bonsái (fase, estilo, objetivo de diseño, calendario de trabajos estacionales), gestiona planes activos (abandono y evaluación), crea trasplantes, elimina trabajos planificados, y abre sesiones de documentación de trabajos planificados (análisis previo a ejecutar un trabajo o registro del resultado tras haberlo realizado). Decide la fecha por defecto (próximo sábado) cuando el usuario no especifica una.",
        instruction=KIKARU_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=tools,
        output_key="cultivation_execution_result",
    )
