from typing import Callable

from google.adk.agents.llm_agent import Agent

from bonsai_sensei.domain.services.single_tool_call_callback import limit_to_single_tool_call
from bonsai_sensei.domain.services.garden.caretaker.apply_fertilizer import create_apply_fertilizer_tool
from bonsai_sensei.domain.services.garden.caretaker.apply_phytosanitary import create_apply_phytosanitary_tool
from bonsai_sensei.domain.services.garden.caretaker.create_pest_event import create_create_pest_event_tool
from bonsai_sensei.domain.services.garden.caretaker.record_transplant import create_record_transplant_tool
from bonsai_sensei.domain.services.garden.caretaker.bonsai_events_tool import create_list_bonsai_events_tool
from bonsai_sensei.domain.services.cultivation.plan.planned_work_tools import create_list_planned_works_tool
from bonsai_sensei.domain.services.garden.caretaker.execute_planned_work import create_execute_planned_work_tool


CARETAKER_INSTRUCTION = """Eres el encargado del historial de cuidados de la colección de bonsáis.

# Comportamiento
- Para registrar un evento o ejecutar un trabajo planificado: llama directamente a la tool con los datos disponibles. Las tools gestionan internamente la confirmación.
- Cuando una herramienta devuelva status 'success' o 'cancelled', responde al usuario sin llamar a más herramientas.
- Cuando una herramienta devuelva status 'error', informa al usuario del motivo sin llamar a otras herramientas ni intentar resolver el problema por otra vía.
- Para ejecutar un trabajo planificado: usa primero list_planned_works_for_bonsai para obtener el ID, luego llama a execute_planned_work.
"""


def create_caretaker(
    model,
    get_bonsai_by_name_func: Callable,
    get_fertilizer_by_name_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    get_pest_by_name_func: Callable,
    list_phytosanitary_func: Callable,
    get_active_phytosanitary_plan_func: Callable,
    record_bonsai_event_func: Callable,
    list_bonsai_events_func: Callable,
    list_planned_works_func: Callable,
    get_planned_work_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    ask_plan_review: Callable,
    build_apply_fertilizer_confirmation: Callable,
    build_apply_phytosanitary_confirmation: Callable,
    build_record_transplant_confirmation: Callable,
    build_execute_planned_work_confirmation: Callable,
    build_create_pest_event_confirmation: Callable,
    build_phytosanitary_plan_review_proposal: Callable,
    build_applied_treatment_question: Callable,
    build_treatment_selection_question: Callable,
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
        record_bonsai_event_func=record_bonsai_event_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_apply_phytosanitary_confirmation,
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
    list_works_tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=list_planned_works_func,
    )
    list_works_tool.__name__ = "list_planned_works_for_bonsai"
    execute_planned_work_tool = create_execute_planned_work_tool(
        get_planned_work_func=get_planned_work_func,
        record_bonsai_event_func=record_bonsai_event_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_execute_planned_work_confirmation,
    )
    execute_planned_work_tool.__name__ = "execute_planned_work"
    pest_event_tool = create_create_pest_event_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_pest_by_name_func=get_pest_by_name_func,
        list_phytosanitary_func=list_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        get_active_phytosanitary_plan_func=get_active_phytosanitary_plan_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        ask_plan_review=ask_plan_review,
        build_confirmation_message=build_create_pest_event_confirmation,
        build_applied_treatment_question=build_applied_treatment_question,
        build_treatment_selection_question=build_treatment_selection_question,
        build_plan_review_proposal=build_phytosanitary_plan_review_proposal,
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
            list_works_tool,
            execute_planned_work_tool,
        ],
    )
