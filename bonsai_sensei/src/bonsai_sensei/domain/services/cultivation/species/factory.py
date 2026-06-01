import os
from functools import partial
from typing import Callable

from bonsai_sensei.domain import herbarium, pest_catalog
from bonsai_sensei.domain import user_settings_store
from bonsai_sensei.domain.services.cultivation.pests.pest_catalog_seeder import create_pest_catalog_seeder
from bonsai_sensei.domain.services.cultivation.pests.pest_wiki_compiler import create_pest_wiki_compiler
from bonsai_sensei.domain.services.cultivation.species.botanist import create_botanist
from bonsai_sensei.domain.services.cultivation.species.list_species import create_list_species_tool
from bonsai_sensei.domain.services.cultivation.species.refresh_species_wiki import create_refresh_species_wiki_tool
from bonsai_sensei.domain.services.cultivation.species.scientific_name import create_scientific_name_resolver
from bonsai_sensei.domain.services.cultivation.species.scientific_name_searcher import create_trefle_searcher
from bonsai_sensei.domain.services.cultivation.species.scientific_name_translator import translate_to_english
from bonsai_sensei.domain.services.cultivation.species.species_wiki_compiler import create_species_wiki_compiler
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import create_tavily_searcher
from bonsai_sensei.infrastructure.wiki_client import create_http_read_wiki_page_tool


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
    build_create_pest_confirmation: Callable,
    build_delete_pest_confirmation: Callable,
    orchestrator_model: object = None,
    register_background_task: Callable | None = None,
):
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
        build_create_pest_confirmation=build_create_pest_confirmation,
        build_delete_pest_confirmation=build_delete_pest_confirmation,
        orchestrator_model=orchestrator_model,
        register_background_task=register_background_task,
    )
    return botanist


def _create_botanist(model, session_factory, ask_confirmation, ask_selection, build_create_species_selection_question, build_create_species_confirmation, build_delete_species_confirmation, build_update_species_confirmation, build_refresh_species_wiki_confirmation, build_create_pest_confirmation, build_delete_pest_confirmation, orchestrator_model=None, register_background_task=None):
    effective_orchestrator_model = orchestrator_model or model
    get_species_by_name_func = partial(herbarium.get_species_by_name, create_session=session_factory)
    search_species_func = partial(herbarium.search_species_by_name, create_session=session_factory)

    trefle_base_url = os.getenv("TREFLE_API_BASE", "https://trefle.io")
    scientific_name_resolver = create_scientific_name_resolver(
        translator=translate_to_english,
        searcher=create_trefle_searcher(os.getenv("TREFLE_API_TOKEN"), trefle_base_url),
    )

    tavily_base_url = os.getenv("TAVILY_API_BASE")
    kb_base_url = os.getenv("KB_BASE_URL", "http://knowledge_base:8080")
    tavily_searcher = create_tavily_searcher(os.getenv("TAVILY_API_KEY"), tavily_base_url)
    wiki_page_builder = create_species_wiki_compiler(
        model=effective_orchestrator_model,
        kb_base_url=kb_base_url,
        searcher=tavily_searcher,
    )
    compile_pest_page = create_pest_wiki_compiler(
        model=effective_orchestrator_model,
        kb_base_url=kb_base_url,
        searcher=tavily_searcher,
    )
    pest_catalog_seeder = create_pest_catalog_seeder(
        model=model,
        searcher=tavily_searcher,
        compile_pest_page=compile_pest_page,
        create_pest_func=partial(pest_catalog.create_pest, create_session=session_factory),
        get_pest_by_name_func=partial(pest_catalog.get_pest_by_name, create_session=session_factory),
    )
    read_wiki_page_tool = create_http_read_wiki_page_tool(kb_base_url)

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
        list_pests_func=partial(pest_catalog.list_pests, create_session=session_factory),
        get_pest_by_name_func=partial(pest_catalog.get_pest_by_name, create_session=session_factory),
        create_pest_func=partial(pest_catalog.create_pest, create_session=session_factory),
        delete_pest_func=partial(pest_catalog.delete_pest, create_session=session_factory),
        compile_pest_page=compile_pest_page,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_species_selection_question=build_create_species_selection_question,
        build_create_species_confirmation=build_create_species_confirmation,
        build_delete_species_confirmation=build_delete_species_confirmation,
        build_update_species_confirmation=build_update_species_confirmation,
        build_refresh_species_wiki_confirmation=build_refresh_species_wiki_confirmation,
        build_create_pest_confirmation=build_create_pest_confirmation,
        build_delete_pest_confirmation=build_delete_pest_confirmation,
        refresh_species_wiki_tool=create_refresh_species_wiki_tool(
            get_species_by_name_func=get_species_by_name_func,
            update_species_func=partial(herbarium.update_species, create_session=session_factory),
            wiki_page_builder=wiki_page_builder,
            ask_confirmation=ask_confirmation,
            build_confirmation_message=build_refresh_species_wiki_confirmation,
        ),
        post_create_species_hook=pest_catalog_seeder,
        register_background_task=register_background_task,
    )


def _create_list_species_tool(session_factory):
    return create_list_species_tool(
        partial(herbarium.get_all_species, create_session=session_factory)
    )
