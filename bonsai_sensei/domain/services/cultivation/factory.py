import os
from functools import partial
from typing import Callable

from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain.services.cultivation.plan.planning_agent import (
    create_planning_agent,
)
from bonsai_sensei.domain.services.cultivation.species.botanist import create_botanist
from bonsai_sensei.domain.services.cultivation.species.species_wiki_compiler import (
    create_species_wiki_compiler,
)
from bonsai_sensei.domain.services.wiki_page_tool import create_read_wiki_page_tool
from bonsai_sensei.domain.services.cultivation.species.scientific_name_searcher import (
    create_trefle_searcher,
)
from bonsai_sensei.domain.services.cultivation.species.scientific_name_tool import (
    create_scientific_name_resolver,
)
from bonsai_sensei.domain.services.cultivation.species.scientific_name_translator import (
    translate_to_english,
)
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import (
    create_tavily_searcher,
)
from bonsai_sensei.domain.services.cultivation.weather.weather_advisor import (
    create_weather_advisor,
)
from bonsai_sensei.domain.services.cultivation.weather.weather_tool import (
    create_weather_tool,
)
from bonsai_sensei.domain.services.cultivation.weather.get_user_location_tool import (
    create_get_user_location_tool,
)
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import (
    create_list_species_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.planned_work_tools import (
    create_list_planned_works_tool,
    create_list_fertilizers_tool,
    create_list_phytosanitary_tool,
    create_list_bonsai_events_tool,
    create_list_weekend_planned_works_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.confirm_create_fertilizer_application_tool import (
    create_confirm_create_fertilizer_application_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.confirm_create_phytosanitary_application_tool import (
    create_confirm_create_phytosanitary_application_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.confirm_create_transplant_tool import (
    create_confirm_create_transplant_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.confirm_delete_planned_work_tool import (
    create_confirm_delete_planned_work_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.fertilizer_advisor import (
    create_fertilizer_advisor,
)
from bonsai_sensei.domain.services.cultivation.plan.phytosanitary_advisor import (
    create_phytosanitary_advisor,
)
from bonsai_sensei.domain.services.garden.bonsai_tools import create_list_bonsai_tool
from bonsai_sensei.domain import user_settings_store


def create_cultivation_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_fertilizer_confirmation: Callable,
    build_phytosanitary_confirmation: Callable,
    build_transplant_confirmation: Callable,
    build_delete_confirmation: Callable,
    build_create_species_confirmation: Callable,
    build_delete_species_confirmation: Callable,
    build_update_species_confirmation: Callable,
    orchestrator_model: object = None,
):
    effective_orchestrator_model = orchestrator_model or model
    list_species_tool = _create_list_species_tool(session_factory=session_factory)
    weather_agent = _create_weather_agent(model, list_species_tool, session_factory)
    botanist = _create_botanist(
        model, session_factory, ask_confirmation, ask_selection,
        build_create_species_confirmation, build_delete_species_confirmation, build_update_species_confirmation,
    )

    list_bonsai_events_tool = _create_list_bonsai_events_tool(session_factory=session_factory)
    fertilizer_advisor = _create_fertilizer_advisor(
        model=model,
        session_factory=session_factory,
        list_bonsai_events_tool=list_bonsai_events_tool,
    )
    phytosanitary_advisor = _create_phytosanitary_advisor(
        model=model,
        session_factory=session_factory,
        list_bonsai_events_tool=list_bonsai_events_tool,
    )

    list_planned_works_tool = _create_list_planned_works_tool(session_factory=session_factory)
    list_planned_works_tool.__name__ = "list_planned_works_for_bonsai"

    confirm_create_fertilizer_tool = _create_confirm_create_fertilizer_application_tool(
        session_factory=session_factory, ask_confirmation=ask_confirmation,
        build_confirmation_message=build_fertilizer_confirmation,
    )
    confirm_create_phytosanitary_tool = _create_confirm_create_phytosanitary_application_tool(
        session_factory=session_factory, ask_confirmation=ask_confirmation,
        build_confirmation_message=build_phytosanitary_confirmation,
    )
    confirm_create_transplant_tool = _create_confirm_create_transplant_tool(
        session_factory=session_factory, ask_confirmation=ask_confirmation,
        build_confirmation_message=build_transplant_confirmation,
    )

    planning_agent = _create_planning_agent(
        model=model,
        orchestrator_model=effective_orchestrator_model,
        fertilizer_advisor=fertilizer_advisor,
        phytosanitary_advisor=phytosanitary_advisor,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        build_delete_confirmation=build_delete_confirmation,
        list_planned_works_tool=list_planned_works_tool,
        list_bonsai_events_tool=list_bonsai_events_tool,
        confirm_create_fertilizer_tool=confirm_create_fertilizer_tool,
        confirm_create_phytosanitary_tool=confirm_create_phytosanitary_tool,
        confirm_create_transplant_tool=confirm_create_transplant_tool,
    )

    return botanist, weather_agent, planning_agent


def _create_botanist(model, session_factory, ask_confirmation, ask_selection, build_create_species_confirmation, build_delete_species_confirmation, build_update_species_confirmation):
    get_species_by_name_func = partial(
        herbarium.get_species_by_name, create_session=session_factory
    )
    search_species_func = partial(
        herbarium.search_species_by_name, create_session=session_factory
    )

    trefle_base_url = os.getenv("TREFLE_API_BASE", "https://trefle.io")
    scientific_name_resolver = create_scientific_name_resolver(
        translator=translate_to_english,
        searcher=create_trefle_searcher(os.getenv("TREFLE_API_TOKEN"), trefle_base_url),
    )

    tavily_base_url = os.getenv("TAVILY_API_BASE")
    wiki_root = os.getenv("WIKI_PATH", "./wiki")
    wiki_page_builder = create_species_wiki_compiler(
        model=model,
        wiki_root=wiki_root,
        searcher=create_tavily_searcher(os.getenv("TAVILY_API_KEY"), tavily_base_url),
    )
    read_wiki_page_tool = create_read_wiki_page_tool(wiki_root=wiki_root)

    return create_botanist(
        model=model,
        get_species_by_name_func=get_species_by_name_func,
        search_species_func=search_species_func,
        scientific_name_resolver=scientific_name_resolver,
        wiki_page_builder=wiki_page_builder,
        read_wiki_page_tool=read_wiki_page_tool,
        create_species_func=partial(
            herbarium.create_species, create_session=session_factory
        ),
        update_species_func=partial(
            herbarium.update_species, create_session=session_factory
        ),
        delete_species_func=partial(
            herbarium.delete_species, create_session=session_factory
        ),
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_species_confirmation=build_create_species_confirmation,
        build_delete_species_confirmation=build_delete_species_confirmation,
        build_update_species_confirmation=build_update_species_confirmation,
    )


def _create_weather_agent(model, list_species_tool, session_factory):
    weather_base_url = os.getenv("WEATHER_API_BASE", "https://wttr.in")
    weather_tool = create_weather_tool(weather_base_url)
    get_user_location_tool = create_get_user_location_tool(
        get_user_settings_func=partial(
            user_settings_store.get_user_settings, create_session=session_factory
        )
    )
    weather_agent = create_weather_advisor(
        model=model,
        tools=[weather_tool, list_species_tool, get_user_location_tool],
    )

    return weather_agent


def _create_list_species_tool(session_factory):
    get_all_species_partial = partial(
        herbarium.get_all_species, create_session=session_factory
    )
    tool = create_list_species_tool(get_all_species_partial)
    return tool


def _create_list_bonsai_events_tool(session_factory):
    return create_list_bonsai_events_tool(
        get_bonsai_by_name_func=partial(
            garden.get_bonsai_by_name, create_session=session_factory
        ),
        list_bonsai_events_func=partial(
            bonsai_history.list_bonsai_events, create_session=session_factory
        ),
    )


def _create_fertilizer_advisor(model, session_factory, list_bonsai_events_tool):
    list_fertilizers_tool = create_list_fertilizers_tool(
        list_fertilizers_func=partial(
            fertilizer_catalog.list_fertilizers, create_session=session_factory
        )
    )
    return create_fertilizer_advisor(
        model=model,
        tools=[list_fertilizers_tool, list_bonsai_events_tool],
    )


def _create_phytosanitary_advisor(model, session_factory, list_bonsai_events_tool):
    list_phytosanitary_tool = create_list_phytosanitary_tool(
        list_phytosanitary_func=partial(
            phytosanitary_registry.list_phytosanitary, create_session=session_factory
        )
    )
    return create_phytosanitary_advisor(
        model=model,
        tools=[list_phytosanitary_tool, list_bonsai_events_tool],
    )


def _create_list_planned_works_tool(session_factory):
    return create_list_planned_works_tool(
        get_bonsai_by_name_func=partial(
            garden.get_bonsai_by_name, create_session=session_factory
        ),
        list_planned_works_func=partial(
            cultivation_plan.list_planned_works, create_session=session_factory
        ),
    )


def _create_confirm_create_fertilizer_application_tool(session_factory, ask_confirmation, build_confirmation_message):
    return create_confirm_create_fertilizer_application_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_fertilizer_by_name_func=partial(fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )


def _create_confirm_create_phytosanitary_application_tool(session_factory, ask_confirmation, build_confirmation_message):
    return create_confirm_create_phytosanitary_application_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        get_phytosanitary_by_name_func=partial(phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )


def _create_confirm_create_transplant_tool(session_factory, ask_confirmation, build_confirmation_message):
    return create_confirm_create_transplant_tool(
        get_bonsai_by_name_func=partial(garden.get_bonsai_by_name, create_session=session_factory),
        create_planned_work_func=partial(cultivation_plan.create_planned_work, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )


def _create_planning_agent(
    model, orchestrator_model, fertilizer_advisor, phytosanitary_advisor, session_factory,
    ask_confirmation, build_delete_confirmation, list_planned_works_tool, list_bonsai_events_tool,
    confirm_create_fertilizer_tool, confirm_create_phytosanitary_tool, confirm_create_transplant_tool,
):
    confirm_delete_tool = create_confirm_delete_planned_work_tool(
        get_planned_work_func=partial(
            cultivation_plan.get_planned_work, create_session=session_factory
        ),
        delete_planned_work_func=partial(
            cultivation_plan.delete_planned_work, create_session=session_factory
        ),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_delete_confirmation,
    )
    list_collection_tool = create_list_bonsai_tool(
        list_bonsai_func=partial(garden.list_bonsai, create_session=session_factory),
        list_species_func=partial(herbarium.list_species, create_session=session_factory),
    )
    list_weekend_tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=partial(
            cultivation_plan.list_planned_works_in_date_range, create_session=session_factory
        ),
        list_bonsai_func=partial(garden.list_bonsai, create_session=session_factory),
    )
    return create_planning_agent(
        model=model,
        orchestrator_model=orchestrator_model,
        fertilizer_advisor=fertilizer_advisor,
        phytosanitary_advisor=phytosanitary_advisor,
        list_planned_works_tool=list_planned_works_tool,
        list_bonsai_events_tool=list_bonsai_events_tool,
        confirm_create_fertilizer_application_tool=confirm_create_fertilizer_tool,
        confirm_create_phytosanitary_application_tool=confirm_create_phytosanitary_tool,
        confirm_create_transplant_tool=confirm_create_transplant_tool,
        confirm_delete_planned_work_tool=confirm_delete_tool,
        list_collection_tool=list_collection_tool,
        list_weekend_planned_works_tool=list_weekend_tool,
    )
