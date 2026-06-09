from functools import partial
from typing import Callable

from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import development_plan_store
from bonsai_sensei.domain import user_settings_store
from bonsai_sensei.domain.services.cultivation.plan.design.manage import create_manage_development_plan_tool
from bonsai_sensei.domain.services.cultivation.plan.design.abandon_plan import create_abandon_development_plan_tool
from bonsai_sensei.domain.services.cultivation.plan.design.evaluate import create_evaluate_development_plan_tool
from bonsai_sensei.domain.services.cultivation.plan.clarification_runner import create_clarification_loop_runner
from bonsai_sensei.domain.services.cultivation.plan.plan_proposal_runner import create_plan_proposal_runner


def create_design_plan_tools(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_human: Callable,
    ask_plan_review: Callable,
    build_abandon_development_plan_confirmation: Callable,
    build_bonsai_name_question: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    orchestrator_model: object = None,
    ask_poll: Callable | None = None,
    search_memory_func: Callable | None = None,
) -> dict:
    effective_model = orchestrator_model or model

    manage_tool = create_manage_development_plan_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
        get_species_by_id_func=partial(herbarium.get_species_by_id, create_session=session_factory),
        get_active_development_plan_func=partial(development_plan_store.get_active_development_plan, create_session=session_factory),
        create_development_plan_func=partial(development_plan_store.create_development_plan, create_session=session_factory),
        update_development_plan_func=partial(development_plan_store.update_development_plan, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        delete_future_planned_works_func=partial(cultivation_plan.delete_future_planned_works_by_development_plan, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        get_user_settings_func=partial(user_settings_store.get_user_settings, create_session=session_factory),
        search_memory_func=search_memory_func,
        run_clarification_loop=create_clarification_loop_runner(
            model=effective_model,
            ask_human=ask_human,
            app_name="design_plan_clarification",
            ask_poll=ask_poll,
        ),
        run_plan_proposal=create_plan_proposal_runner(
            model=effective_model,
            ask_human=ask_human,
            ask_plan_review=ask_plan_review,
            app_name="design_plan_proposal",
        ),
    )

    abandon_tool = create_abandon_development_plan_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_active_development_plan_func=partial(development_plan_store.get_active_development_plan, create_session=session_factory),
        update_development_plan_func=partial(development_plan_store.update_development_plan, create_session=session_factory),
        delete_future_planned_works_func=partial(cultivation_plan.delete_future_planned_works_by_development_plan, create_session=session_factory),
        record_bonsai_event_func=partial(bonsai_history.record_bonsai_event, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_abandon_development_plan_confirmation,
    )

    evaluate_tool = create_evaluate_development_plan_tool(
        model=effective_model,
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_active_development_plan_func=partial(development_plan_store.get_active_development_plan, create_session=session_factory),
        list_bonsai_events_func=partial(bonsai_history.list_bonsai_events, create_session=session_factory),
        read_wiki_page_func=read_wiki_page_func,
        list_wiki_files_func=list_wiki_files_func,
        ask_human=ask_human,
        build_bonsai_name_question=build_bonsai_name_question,
    )

    return {
        "manage_development_plan": manage_tool,
        "abandon_development_plan": abandon_tool,
        "evaluate_development_plan": evaluate_tool,
    }
