import os
from functools import partial

from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain.services.cultivation.cultivation_agent import (
    create_cultivation_agent,
)
from bonsai_sensei.domain.services.cultivation.species.botanist import create_botanist
from bonsai_sensei.domain.services.cultivation.species.care_guide_agent import (
    create_care_guide_agent,
)
from bonsai_sensei.domain.services.cultivation.species.care_guide_service import (
    create_care_guide_builder,
)
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
)
from bonsai_sensei.domain.services.cultivation.plan.confirm_create_planned_work_tool import (
    create_confirm_create_planned_work_tool,
)
from bonsai_sensei.domain.services.cultivation.plan.fertilizer_advisor import (
    create_fertilizer_advisor,
)
from bonsai_sensei.domain.services.cultivation.plan.phytosanitary_advisor import (
    create_phytosanitary_advisor,
)
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain import user_settings_store


def create_cultivation_group(
    model: object,
    session_factory,
    confirmation_store: ConfirmationStore | None = None,
):
    list_species_tool = _create_list_species_tool(session_factory=session_factory)
    weather_agent = _create_weather_agent(model, list_species_tool, session_factory)
    botanist = _create_botanist(
        model, session_factory, confirmation_store, list_species_tool
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
    confirm_create_tool = _create_confirm_create_planned_work_tool(
        session_factory=session_factory,
        confirmation_store=confirmation_store,
    )
    list_planned_works_tool.__name__ = "list_planned_works_for_bonsai"
    confirm_create_tool.__name__ = "confirm_create_planned_work"

    return create_cultivation_agent(
        model=model,
        botanist=botanist,
        weather_advisor=weather_agent,
        fertilizer_advisor=fertilizer_advisor,
        phytosanitary_advisor=phytosanitary_advisor,
        list_planned_works_tool=list_planned_works_tool,
        confirm_create_planned_work_tool=confirm_create_tool,
    )


def _create_botanist(model, session_factory, confirmation_store, list_species_tool):
    get_species_by_name_func = partial(
        herbarium.get_species_by_name, create_session=session_factory
    )

    trefle_base_url = os.getenv("TREFLE_API_BASE", "https://trefle.io")
    trefle_searcher = create_trefle_searcher(
        os.getenv("TREFLE_API_TOKEN"), trefle_base_url
    )
    resolve_name_tool = create_scientific_name_resolver(
        translator=translate_to_english,
        searcher=trefle_searcher,
    )

    tavily_base_url = os.getenv("TAVILY_API_BASE")
    tavily_searcher = create_tavily_searcher(
        os.getenv("TAVILY_API_KEY"), tavily_base_url
    )
    care_guide_builder = create_care_guide_builder(tavily_searcher)

    care_guide_agent = create_care_guide_agent(
        model=model,
        tools=[care_guide_builder],
    )

    botanist = create_botanist(
        model=model,
        get_species_by_name_func=get_species_by_name_func,
        resolve_scientific_name=resolve_name_tool,
        list_species=list_species_tool,
        care_guide_agent=care_guide_agent,
        create_species_func=partial(
            herbarium.create_species, create_session=session_factory
        ),
        update_species_func=partial(
            herbarium.update_species, create_session=session_factory
        ),
        delete_species_func=partial(
            herbarium.delete_species, create_session=session_factory
        ),
        confirmation_store=confirmation_store,
    )

    return botanist


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


def _create_confirm_create_planned_work_tool(session_factory, confirmation_store):
    return create_confirm_create_planned_work_tool(
        get_bonsai_by_name_func=partial(
            garden.get_bonsai_by_name, create_session=session_factory
        ),
        get_fertilizer_by_name_func=partial(
            fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory
        ),
        get_phytosanitary_by_name_func=partial(
            phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory
        ),
        create_planned_work_func=partial(
            cultivation_plan.create_planned_work, create_session=session_factory
        ),
        confirmation_store=confirmation_store,
    )
