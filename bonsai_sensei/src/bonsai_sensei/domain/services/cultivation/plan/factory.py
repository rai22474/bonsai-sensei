import os
from functools import partial
from typing import Callable

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import fertilization_plan_store
from bonsai_sensei.domain import phytosanitary_plan_store
from bonsai_sensei.domain.services.cultivation.plan.kikaru import create_kikaru
from bonsai_sensei.domain.services.cultivation.plan.fertilization.create_fertilizer_application import (
    create_create_fertilizer_application_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.fertilization.schedule_fertilization import (
    create_schedule_fertilization_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.phytosanitary.schedule_phytosanitary import (
    create_schedule_phytosanitary_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.phytosanitary.create_phytosanitary_application import (
    create_create_phytosanitary_application_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.works.create_transplant import create_create_transplant_tool
from bonsai_sensei.domain.services.cultivation.plan.works.delete_planned_work import create_delete_planned_work_tool
from bonsai_sensei.domain.services.cultivation.plan.works.list_planned_works import create_list_planned_works_tool
from bonsai_sensei.domain.services.cultivation.plan.fertilization.manage import (
    create_manage_fertilization_plan_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.fertilization.abandon_plan import (
    create_abandon_fertilization_plan_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.fertilization.evaluate import (
    create_evaluate_fertilization_plan_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.design.factory import create_design_plan_tools
from bonsai_sensei.infrastructure.wiki_client import (
    create_http_read_wiki_page_tool,
    create_http_write_wiki_page_tool,
    create_http_list_wiki_files_tool,
)


def create_kikaru_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_human: Callable,
    ask_selection: Callable,
    ask_plan_review: Callable,
    build_fertilizer_selection_question: Callable,
    build_fertilization_type_question: Callable,
    build_fertilization_type_options: Callable,
    build_period_question: Callable,
    build_phytosanitary_type_question: Callable,
    build_phytosanitary_type_options: Callable,
    build_phytosanitary_period_question: Callable,
    build_fertilizer_confirmation: Callable,
    build_phytosanitary_confirmation: Callable,
    build_transplant_confirmation: Callable,
    build_delete_confirmation: Callable,
    build_abandon_plan_confirmation: Callable,
    build_abandon_phytosanitary_plan_confirmation: Callable,
    build_abandon_development_plan_confirmation: Callable,
    build_bonsai_name_question: Callable,
    orchestrator_model: object = None,
    ask_poll: Callable | None = None,
):
    effective_orchestrator_model = orchestrator_model or model
    kb_base_url = os.getenv("KB_BASE_URL", "http://knowledge_base:8080")
    read_wiki_page_func = create_http_read_wiki_page_tool(kb_base_url)
    write_wiki_page_func = create_http_write_wiki_page_tool(kb_base_url)
    list_wiki_files_func = create_http_list_wiki_files_tool(kb_base_url)

    manage_fertilization_plan_tool = _create_manage_fertilization_plan_tool(
        model=effective_orchestrator_model,
        session_factory=session_factory,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_plan_review=ask_plan_review,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        ask_poll=ask_poll,
    )
    abandon_fertilization_plan_tool = _create_abandon_fertilization_plan_tool(
        session_factory=session_factory,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_abandon_plan_confirmation,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
    )
    evaluate_fertilization_plan_tool = create_evaluate_fertilization_plan_tool(
        model=effective_orchestrator_model,
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_active_fertilization_plan_func=partial(fertilization_plan_store.get_active_fertilization_plan, create_session=session_factory),
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )
    manage_phytosanitary_plan_tool = _create_manage_phytosanitary_plan_tool(
        model=effective_orchestrator_model,
        session_factory=session_factory,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_plan_review=ask_plan_review,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        ask_poll=ask_poll,
    )
    abandon_phytosanitary_plan_tool = _create_abandon_phytosanitary_plan_tool(
        session_factory=session_factory,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_abandon_phytosanitary_plan_confirmation,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
    )
    evaluate_phytosanitary_plan_tool = _create_evaluate_phytosanitary_plan_tool(
        model=effective_orchestrator_model,
        session_factory=session_factory,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        read_wiki_page_func=read_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
    )
    create_fertilizer_tool = create_create_fertilizer_application_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_fertilizer_by_name_func=partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory),
        list_fertilizers_func=partial(fertilizer_catalog.list_fertilizers, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_confirmation_message=build_fertilizer_confirmation,
        build_selection_question=build_fertilizer_selection_question,
    )
    schedule_fertilization_tool = create_schedule_fertilization_tool(
        run_one_time_func=create_fertilizer_tool,
        run_plan_func=manage_fertilization_plan_tool,
        ask_selection=ask_selection,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        build_type_question=build_fertilization_type_question,
        build_type_options=build_fertilization_type_options,
        build_period_question=build_period_question,
    )

    create_phytosanitary_tool = create_create_phytosanitary_application_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_phytosanitary_by_name_func=partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_phytosanitary_confirmation,
    )
    schedule_phytosanitary_tool = create_schedule_phytosanitary_tool(
        run_one_time_func=create_phytosanitary_tool,
        run_plan_func=manage_phytosanitary_plan_tool,
        ask_selection=ask_selection,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        build_type_question=build_phytosanitary_type_question,
        build_type_options=build_phytosanitary_type_options,
        build_period_question=build_phytosanitary_period_question,
    )
    create_transplant_tool = create_create_transplant_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_transplant_confirmation,
    )

    delete_planned_work_tool = create_delete_planned_work_tool(
        get_planned_work_func=partial(cultivation_plan.get_planned_work, create_session=session_factory),
        delete_planned_work_func=partial(cultivation_plan.delete_planned_work, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_delete_confirmation,
    )
    list_planned_works_tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        list_planned_works_in_date_range_func=partial(cultivation_plan.list_planned_works_in_date_range, create_session=session_factory),
    )
    design_tools = create_design_plan_tools(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_human=ask_human,
        ask_plan_review=ask_plan_review,
        build_abandon_development_plan_confirmation=build_abandon_development_plan_confirmation,
        build_bonsai_name_question=build_bonsai_name_question,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        orchestrator_model=effective_orchestrator_model,
        ask_poll=ask_poll,
    )

    return create_kikaru(
        model=model,
        schedule_fertilization_tool=schedule_fertilization_tool,
        abandon_fertilization_plan_tool=abandon_fertilization_plan_tool,
        evaluate_fertilization_plan_tool=evaluate_fertilization_plan_tool,
        schedule_phytosanitary_tool=schedule_phytosanitary_tool,
        abandon_phytosanitary_plan_tool=abandon_phytosanitary_plan_tool,
        evaluate_phytosanitary_plan_tool=evaluate_phytosanitary_plan_tool,
        manage_development_plan_tool=design_tools["manage_development_plan"],
        abandon_development_plan_tool=design_tools["abandon_development_plan"],
        evaluate_development_plan_tool=design_tools["evaluate_development_plan"],
        create_transplant_tool=create_transplant_tool,
        delete_planned_work_tool=delete_planned_work_tool,
        list_planned_works_tool=list_planned_works_tool,
    )


def _create_manage_fertilization_plan_tool(model, session_factory, ask_human, build_bonsai_name_question, ask_plan_review, read_wiki_page_func, write_wiki_page_func, list_wiki_files_func: Callable, ask_poll: Callable | None = None):
    from bonsai_sensei.domain.services.cultivation.plan.plan_proposal_runner import create_plan_proposal_runner as create_fertilization_plan_runner
    from bonsai_sensei.domain.services.cultivation.plan.clarification_runner import create_clarification_loop_runner
    return create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
        list_fertilizers_func=partial(fertilizer_catalog.list_fertilizers, create_session=session_factory),
        get_fertilizer_by_name_func=partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory),
        get_active_fertilization_plan_func=partial(fertilization_plan_store.get_active_fertilization_plan, create_session=session_factory),
        create_fertilization_plan_func=partial(fertilization_plan_store.create_fertilization_plan, create_session=session_factory),
        update_fertilization_plan_func=partial(fertilization_plan_store.update_fertilization_plan, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        delete_future_planned_works_func=partial(cultivation_plan.delete_future_planned_works_by_plan, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        run_clarification_loop=create_clarification_loop_runner(model=model, ask_human=ask_human, app_name="fertilization_plan_clarification", ask_poll=ask_poll),
        run_plan_proposal=create_fertilization_plan_runner(model=model, ask_human=ask_human, ask_plan_review=ask_plan_review, app_name="fertilization_plan_proposal"),
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )


def _create_abandon_fertilization_plan_tool(session_factory, ask_human, build_bonsai_name_question, ask_confirmation, build_confirmation_message, read_wiki_page_func, write_wiki_page_func):
    return create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_active_fertilization_plan_func=partial(fertilization_plan_store.get_active_fertilization_plan, create_session=session_factory),
        update_fertilization_plan_func=partial(fertilization_plan_store.update_fertilization_plan, create_session=session_factory),
        delete_future_planned_works_func=partial(cultivation_plan.delete_future_planned_works_by_plan, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )



def _create_manage_phytosanitary_plan_tool(model, session_factory, ask_human, build_bonsai_name_question, ask_plan_review, read_wiki_page_func, write_wiki_page_func, list_wiki_files_func: Callable, ask_poll: Callable | None = None):
    from bonsai_sensei.domain.services.cultivation.plan.phytosanitary.manage import create_manage_phytosanitary_plan_tool
    from bonsai_sensei.domain.services.cultivation.plan.clarification_runner import create_clarification_loop_runner
    from bonsai_sensei.domain.services.cultivation.plan.plan_proposal_runner import create_plan_proposal_runner
    return create_manage_phytosanitary_plan_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
        list_phytosanitary_func=partial(phytosanitary_registry.list_phytosanitary, create_session=session_factory),
        get_phytosanitary_by_name_func=partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory),
        get_active_phytosanitary_plan_func=partial(phytosanitary_plan_store.get_active_phytosanitary_plan, create_session=session_factory),
        create_phytosanitary_plan_func=partial(phytosanitary_plan_store.create_phytosanitary_plan, create_session=session_factory),
        update_phytosanitary_plan_func=partial(phytosanitary_plan_store.update_phytosanitary_plan, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        delete_future_planned_works_func=partial(cultivation_plan.delete_future_planned_works_by_phytosanitary_plan, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        run_clarification_loop=create_clarification_loop_runner(model=model, ask_human=ask_human, app_name="phytosanitary_plan_clarification", ask_poll=ask_poll),
        run_plan_proposal=create_plan_proposal_runner(model=model, ask_human=ask_human, ask_plan_review=ask_plan_review, app_name="phytosanitary_plan_proposal"),
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )


def _create_abandon_phytosanitary_plan_tool(session_factory, ask_human, build_bonsai_name_question, ask_confirmation, build_confirmation_message, read_wiki_page_func, write_wiki_page_func):
    from bonsai_sensei.domain.services.cultivation.plan.phytosanitary.abandon_plan import create_abandon_phytosanitary_plan_tool
    return create_abandon_phytosanitary_plan_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_active_phytosanitary_plan_func=partial(phytosanitary_plan_store.get_active_phytosanitary_plan, create_session=session_factory),
        update_phytosanitary_plan_func=partial(phytosanitary_plan_store.update_phytosanitary_plan, create_session=session_factory),
        delete_future_planned_works_func=partial(cultivation_plan.delete_future_planned_works_by_phytosanitary_plan, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )


def _create_evaluate_phytosanitary_plan_tool(model, session_factory, ask_human, build_bonsai_name_question, read_wiki_page_func, list_wiki_files_func):
    from bonsai_sensei.domain.services.cultivation.plan.phytosanitary.evaluate import create_evaluate_phytosanitary_plan_tool
    return create_evaluate_phytosanitary_plan_tool(
        model=model,
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_active_phytosanitary_plan_func=partial(phytosanitary_plan_store.get_active_phytosanitary_plan, create_session=session_factory),
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )
