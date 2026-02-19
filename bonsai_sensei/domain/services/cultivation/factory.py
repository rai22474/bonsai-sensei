import os
from functools import partial

from bonsai_sensei.domain import herbarium
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
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import (
    create_list_species_tool,
)
from bonsai_sensei.domain.confirmation_store import ConfirmationStore


def create_cultivation_group(
    model: object,
    session_factory,
    confirmation_store: ConfirmationStore | None = None,
):
    list_species_tool = _create_list_species_tool(session_factory=session_factory)

    weather_agent = _create_weather_agent(model, list_species_tool)

    botanist = _create_botanist(
        model, session_factory, confirmation_store, list_species_tool
    )

    return create_cultivation_agent(
        model=model,
        botanist=botanist,
        weather_advisor=weather_agent,
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


def _create_weather_agent(model, list_species_tool):
    weather_base_url = os.getenv("WEATHER_API_BASE", "https://wttr.in")
    weather_tool = create_weather_tool(weather_base_url)
    weather_agent = create_weather_advisor(
        model=model,
        tools=[weather_tool, list_species_tool],
    )

    return weather_agent


def _create_list_species_tool(session_factory):
    get_all_species_partial = partial(
        herbarium.get_all_species, create_session=session_factory
    )
    tool = create_list_species_tool(get_all_species_partial)
    return tool
