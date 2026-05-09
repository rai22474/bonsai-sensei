import os
from functools import partial
from typing import Callable

from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import user_settings_store
from bonsai_sensei.domain.services.cultivation.species.botanist import create_botanist
from bonsai_sensei.domain.services.cultivation.species.herbarium_tools import create_list_species_tool
from bonsai_sensei.domain.services.cultivation.species.refresh_species_wiki import create_refresh_species_wiki_tool
from bonsai_sensei.domain.services.cultivation.species.scientific_name import create_scientific_name_resolver
from bonsai_sensei.domain.services.cultivation.species.scientific_name_searcher import create_trefle_searcher
from bonsai_sensei.domain.services.cultivation.species.scientific_name_translator import translate_to_english
from bonsai_sensei.domain.services.cultivation.species.species_wiki_compiler import create_species_wiki_compiler
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import create_tavily_searcher
from bonsai_sensei.domain.services.cultivation.weather.get_user_location import create_get_user_location_tool
from bonsai_sensei.domain.services.cultivation.weather.weather import create_weather_tool
from bonsai_sensei.domain.services.cultivation.weather.weather_advisor import create_weather_advisor
from bonsai_sensei.domain.services.wiki_page import create_read_wiki_page_tool


def create_botanist_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_create_species_selection_question: Callable,
    build_create_species_confirmation: Callable,
    build_delete_species_confirmation: Callable,
    build_update_species_confirmation: Callable,
    build_refresh_species_wiki_confirmation: Callable,
):
    list_species_tool = _create_list_species_tool(session_factory)
    botanist = _create_botanist(
        model=model,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_species_selection_question=build_create_species_selection_question,
        build_create_species_confirmation=build_create_species_confirmation,
        build_delete_species_confirmation=build_delete_species_confirmation,
        build_update_species_confirmation=build_update_species_confirmation,
        build_refresh_species_wiki_confirmation=build_refresh_species_wiki_confirmation,
    )
    weather_advisor = _create_weather_advisor(model, list_species_tool, session_factory)
    return botanist, weather_advisor


def _create_botanist(model, session_factory, ask_confirmation, ask_selection, build_create_species_selection_question, build_create_species_confirmation, build_delete_species_confirmation, build_update_species_confirmation, build_refresh_species_wiki_confirmation):
    get_species_by_name_func = partial(herbarium.get_species_by_name, create_session=session_factory)
    search_species_func = partial(herbarium.search_species_by_name, create_session=session_factory)

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
        create_species_func=partial(herbarium.create_species, create_session=session_factory),
        update_species_func=partial(herbarium.update_species, create_session=session_factory),
        delete_species_func=partial(herbarium.delete_species, create_session=session_factory),
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_species_selection_question=build_create_species_selection_question,
        build_create_species_confirmation=build_create_species_confirmation,
        build_delete_species_confirmation=build_delete_species_confirmation,
        build_update_species_confirmation=build_update_species_confirmation,
        build_refresh_species_wiki_confirmation=build_refresh_species_wiki_confirmation,
        refresh_species_wiki_tool=create_refresh_species_wiki_tool(
            get_species_by_name_func=get_species_by_name_func,
            update_species_func=partial(herbarium.update_species, create_session=session_factory),
            wiki_page_builder=wiki_page_builder,
            ask_confirmation=ask_confirmation,
            build_confirmation_message=build_refresh_species_wiki_confirmation,
        ),
    )


def _create_list_species_tool(session_factory):
    return create_list_species_tool(
        partial(herbarium.get_all_species, create_session=session_factory)
    )


def _create_weather_advisor(model, list_species_tool, session_factory):
    weather_base_url = os.getenv("WEATHER_API_BASE", "https://wttr.in")
    return create_weather_advisor(
        model=model,
        tools=[
            create_weather_tool(weather_base_url),
            list_species_tool,
            create_get_user_location_tool(
                get_user_settings_func=partial(user_settings_store.get_user_settings, create_session=session_factory)
            ),
        ],
    )
