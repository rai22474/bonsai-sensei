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

# Programar fertilización
Si el usuario quiere programar una fertilización (puntual o plan): llama directamente a la herramienta de programación de fertilización con los parámetros que el usuario haya indicado (fecha puntual, período inicio/fin, fertilizante, cantidad). No preguntes antes de actuar — la herramienta gestiona lo que falte.
- Para abandonar el plan de fertilización activo: usa la herramienta de abandono de fertilización indicando el motivo.
- Para evaluar si el plan de fertilización vigente sigue siendo válido: usa la herramienta de evaluación de fertilización.

# Programar tratamiento fitosanitario
Esta sección aplica ÚNICAMENTE cuando el usuario quiere programar o registrar un tratamiento con fecha. No aplica a peticiones de consejo o recomendación.
Si el usuario quiere programar un tratamiento fitosanitario (puntual o plan): llama directamente a la herramienta de programación fitosanitaria con los parámetros que el usuario haya indicado (fecha puntual, período inicio/fin, producto, cantidad). No preguntes antes de actuar — la herramienta gestiona lo que falte.
- Para abandonar el plan fitosanitario activo: usa la herramienta de abandono fitosanitario indicando el motivo.
- Para evaluar si el plan fitosanitario vigente sigue siendo válido: usa la herramienta de evaluación fitosanitaria.

# Eliminar trabajo planificado
Para eliminar un trabajo planificado: primero lista los trabajos del bonsái para obtener el ID, luego llama a la herramienta de eliminación con ese ID.

# Otros trabajos
- Trasplante: crea la tarea directamente. Usa la fecha que el usuario indique, o el próximo sábado si no especifica.

# Formato
Responde siempre en castellano.
"""


def create_kikaru(
    model: object,

    schedule_fertilization_tool: Callable | None = None,
    abandon_fertilization_plan_tool: Callable | None = None,
    evaluate_fertilization_plan_tool: Callable | None = None,
    schedule_phytosanitary_tool: Callable | None = None,
    abandon_phytosanitary_plan_tool: Callable | None = None,
    evaluate_phytosanitary_plan_tool: Callable | None = None,
    create_transplant_tool: Callable | None = None,
    delete_planned_work_tool: Callable | None = None,
    list_planned_works_tool: Callable | None = None,
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
            create_transplant_tool,
            delete_planned_work_tool,
            list_planned_works_tool,
        ]
        if tool is not None
    ]

    return LlmAgent(
        model=model,
        name="kikaru",
        description="Programa fertilizaciones y tratamientos fitosanitarios (puntuales o por período), gestiona planes activos (abandono y evaluación), crea trasplantes, y elimina trabajos planificados. Decide la fecha por defecto (próximo sábado) cuando el usuario no especifica una.",
        instruction=KIKARU_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=tools,
        output_key="cultivation_execution_result",
    )
