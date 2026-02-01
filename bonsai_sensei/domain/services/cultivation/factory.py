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
    trefle_search,
)
from bonsai_sensei.domain.services.cultivation.species.scientific_name_tool import (
    create_scientific_name_resolver,
    resolve_scientific_name,
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
from bonsai_sensei.domain.services.cultivation.weather.weather_tool import get_weather
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import (
    create_list_species_tool,
)


def create_cultivation_group(
    model: object,
    session_factory,
):
    list_species_tool = _create_list_species_tool(session_factory=session_factory)
    create_species_func = partial(
        herbarium.create_species, create_session=session_factory
    )
    update_species_func = partial(
        herbarium.update_species, create_session=session_factory
    )
    delete_species_func = partial(
        herbarium.delete_species, create_session=session_factory
    )
    get_species_by_name_func = partial(
        herbarium.get_species_by_name, create_session=session_factory
    )
    weather_agent = create_weather_advisor(
        model=model,
        tools=[get_weather, list_species_tool],
    )
    resolve_name_tool = create_scientific_name_resolver(
        translator=translate_to_english,
        searcher=trefle_search,
    )
    resolve_name_tool = _with_tool_metadata(
        resolve_name_tool, "resolve_bonsai_scientific_names", resolve_scientific_name
    )
    tavily_searcher = create_tavily_searcher(os.getenv("TAVILY_API_KEY"))
    care_guide_builder = create_care_guide_builder(tavily_searcher)
    care_guide_builder = _with_tool_metadata(
        care_guide_builder, "build_bonsai_care_guide", care_guide_builder
    )
    care_guide_agent = create_care_guide_agent(
        model=model,
        tools=[care_guide_builder],
    )
    species_agent = create_botanist(
        model=model,
        create_species_func=create_species_func,
        update_species_func=update_species_func,
        delete_species_func=delete_species_func,
        get_species_by_name_func=get_species_by_name_func,
        resolve_scientific_name=resolve_name_tool,
        list_species=list_species_tool,
        care_guide_agent=care_guide_agent,
    )
    return create_cultivation_agent(
        model=model,
        botanist=species_agent,
        weather_advisor=weather_agent,
    )


def _create_list_species_tool(session_factory):
    get_all_species_partial = partial(
        herbarium.get_all_species, create_session=session_factory
    )
    tool = create_list_species_tool(get_all_species_partial)
    tool.__name__ = "list_bonsai_species"
    return tool


def _with_tool_metadata(tool, name: str, doc_source):
    tool.__name__ = name
    tool.__doc__ = doc_source.__doc__
    return tool
