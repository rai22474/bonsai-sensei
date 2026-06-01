from functools import partial
from typing import Callable

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import phytosanitary_plan_store
from bonsai_sensei.domain import pest_catalog
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain.services.garden.caretaker.caretaker import create_caretaker
from bonsai_sensei.telegram.messages.garden_messages import (
    build_link_pest_event_selection_question,
    build_pest_event_selection_option,
    NO_LINK_OPTION,
)


def create_caretaker_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_apply_fertilizer_confirmation: Callable,
    build_apply_phytosanitary_confirmation: Callable,
    build_record_transplant_confirmation: Callable,
    build_execute_planned_work_confirmation: Callable,
    build_execute_planned_work_selection_question: Callable,
    build_execute_planned_work_option_label: Callable,
    build_create_pest_event_confirmation: Callable,
):
    get_bonsai_by_name_func = partial(garden.get_bonsai_by_name, create_session=session_factory)
    get_fertilizer_by_name_func = partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory)
    get_phytosanitary_by_name_func = partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory)
    get_pest_by_name_func = partial(pest_catalog.get_pest_by_name, create_session=session_factory)
    get_active_phytosanitary_plan_func = partial(phytosanitary_plan_store.get_active_phytosanitary_plan, create_session=session_factory)
    get_recent_unlinked_pest_events_func = partial(bonsai_history.get_recent_unlinked_pest_events, create_session=session_factory)
    record_bonsai_event_func = partial(bonsai_history.record_bonsai_event, create_session=session_factory)
    list_bonsai_events_func = partial(bonsai_history.list_bonsai_events, create_session=session_factory)
    list_planned_works_func = partial(cultivation_plan.list_planned_works, create_session=session_factory)
    delete_planned_work_func = partial(cultivation_plan.delete_planned_work, create_session=session_factory)

    return create_caretaker(
        model=model,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        get_pest_by_name_func=get_pest_by_name_func,
        get_active_phytosanitary_plan_func=get_active_phytosanitary_plan_func,
        get_recent_unlinked_pest_events_func=get_recent_unlinked_pest_events_func,
        record_bonsai_event_func=record_bonsai_event_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_planned_works_func=list_planned_works_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_apply_fertilizer_confirmation=build_apply_fertilizer_confirmation,
        build_apply_phytosanitary_confirmation=build_apply_phytosanitary_confirmation,
        build_record_transplant_confirmation=build_record_transplant_confirmation,
        build_execute_planned_work_confirmation=build_execute_planned_work_confirmation,
        build_execute_planned_work_selection_question=build_execute_planned_work_selection_question,
        build_execute_planned_work_option_label=build_execute_planned_work_option_label,
        build_create_pest_event_confirmation=build_create_pest_event_confirmation,
        build_link_pest_event_selection_question=build_link_pest_event_selection_question,
        build_pest_event_selection_option=build_pest_event_selection_option,
        no_link_option=NO_LINK_OPTION,
    )
