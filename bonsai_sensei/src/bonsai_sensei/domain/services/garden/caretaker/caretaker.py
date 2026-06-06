from typing import Callable

from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.garden.caretaker.apply_fertilizer import create_apply_fertilizer_tool
from bonsai_sensei.domain.services.garden.caretaker.apply_phytosanitary import create_apply_phytosanitary_tool
from bonsai_sensei.domain.services.garden.caretaker.create_pest_event import create_create_pest_event_tool
from bonsai_sensei.domain.services.garden.caretaker.record_transplant import create_record_transplant_tool
from bonsai_sensei.domain.services.garden.caretaker.bonsai_events_tool import create_list_bonsai_events_tool
from bonsai_sensei.domain.services.garden.caretaker.execute_planned_work import create_execute_planned_work_tool
from bonsai_sensei.domain.services.tool_contract import TOOL_CONTRACT


CARETAKER_INSTRUCTION = f"""Eres el encargado del historial de cuidados de la colección de bonsáis.

# Comportamiento
{TOOL_CONTRACT}
- Si el usuario menciona que ha ejecutado o completado un trabajo planificado, usa la herramienta de ejecución de trabajos planificados — nunca la de aplicación directa de fertilizante o fitosanitario.
- Tras registrar con éxito una detección de plaga, informa brevemente al usuario del resultado. Si la herramienta devuelve active_plan=true, menciona que hay un plan fitosanitario activo que podría necesitar revisión. No hagas preguntas — limítate a informar y dejar que el usuario decida el siguiente paso.
"""


def create_caretaker(
    model,
    get_bonsai_by_name_func: Callable,
    get_fertilizer_by_name_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    get_pest_by_name_func: Callable,
    get_active_phytosanitary_plan_func: Callable,
    get_recent_unlinked_pest_events_func: Callable,
    record_bonsai_event_func: Callable,
    list_bonsai_events_func: Callable,
    list_planned_works_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_apply_fertilizer_confirmation: Callable,
    build_apply_phytosanitary_confirmation: Callable,
    build_record_transplant_confirmation: Callable,
    build_execute_planned_work_confirmation: Callable,
    build_execute_planned_work_selection_question: Callable,
    build_execute_planned_work_option_label: Callable,
    build_create_pest_event_confirmation: Callable,
    build_link_pest_event_selection_question: Callable,
    build_pest_event_selection_option: Callable,
    no_link_option: str,
    get_development_plan_func: Callable | None = None,
) -> Agent:
    apply_fertilizer_tool = create_apply_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_apply_fertilizer_confirmation,
    )
    apply_fertilizer_tool.__name__ = "apply_fertilizer"
    apply_phytosanitary_tool = create_apply_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        get_recent_unlinked_pest_events_func=get_recent_unlinked_pest_events_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_confirmation_message=build_apply_phytosanitary_confirmation,
        build_link_selection_question=build_link_pest_event_selection_question,
        build_pest_event_option=build_pest_event_selection_option,
        no_link_option=no_link_option,
    )
    apply_phytosanitary_tool.__name__ = "apply_phytosanitary"
    record_transplant_tool = create_record_transplant_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_record_transplant_confirmation,
    )
    record_transplant_tool.__name__ = "record_transplant"
    list_events_tool = create_list_bonsai_events_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
    )
    list_events_tool.__name__ = "list_bonsai_events"
    execute_planned_work_tool = create_execute_planned_work_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=list_planned_works_func,
        record_bonsai_event_func=record_bonsai_event_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_confirmation_message=build_execute_planned_work_confirmation,
        build_selection_question=build_execute_planned_work_selection_question,
        build_work_option_label=build_execute_planned_work_option_label,
        get_development_plan_func=get_development_plan_func,
    )
    execute_planned_work_tool.__name__ = "execute_planned_work_for_bonsai"
    pest_event_tool = create_create_pest_event_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_pest_by_name_func=get_pest_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        get_active_phytosanitary_plan_func=get_active_phytosanitary_plan_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_create_pest_event_confirmation,
    )
    pest_event_tool.__name__ = "create_pest_event"
    return Agent(
        model=model,
        name="caretaker",
        description="Registra cuidados realizados en bonsáis: fertilizaciones, tratamientos fitosanitarios, trasplantes, detección de plagas (incluyendo plagas no registradas en el catálogo), y ejecuta trabajos planificados. Es el único agente que debe recibir solicitudes de registro de eventos de cuidado, aunque la plaga o producto no esté en el catálogo.",
        instruction=CARETAKER_INSTRUCTION,
        after_model_callback=limit_to_single_tool_call,
        tools=[
            apply_fertilizer_tool,
            apply_phytosanitary_tool,
            pest_event_tool,
            record_transplant_tool,
            list_events_tool,
            execute_planned_work_tool,
        ],
    )
