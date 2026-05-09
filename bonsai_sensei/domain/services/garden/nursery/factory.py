import os
from functools import partial
from typing import Callable

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain.services.garden.nursery.nursery import create_nursery
from bonsai_sensei.domain.services.wiki_page import create_write_wiki_page_tool


def create_nursery_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_create_bonsai_confirmation: Callable,
    build_delete_bonsai_confirmation: Callable,
    build_update_bonsai_confirmation: Callable,
    build_create_bonsai_species_selection_question: Callable = None,
):
    list_bonsai_func = partial(garden.list_bonsai, create_session=session_factory)
    get_bonsai_by_name_func = partial(garden.get_bonsai_by_name, create_session=session_factory)
    create_bonsai_func = partial(garden.create_bonsai, create_session=session_factory)
    update_bonsai_func = partial(garden.update_bonsai, create_session=session_factory)
    delete_bonsai_func = partial(garden.delete_bonsai, create_session=session_factory)
    list_species_func = partial(herbarium.list_species, create_session=session_factory)
    get_species_by_name_func = partial(herbarium.get_species_by_name, create_session=session_factory)
    wiki_root = os.getenv("WIKI_PATH", "./wiki")
    write_wiki_page_func = create_write_wiki_page_tool(wiki_root=wiki_root)

    return create_nursery(
        model=model,
        list_bonsai_func=list_bonsai_func,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_species_func=list_species_func,
        get_species_by_name_func=get_species_by_name_func,
        create_bonsai_func=create_bonsai_func,
        update_bonsai_func=update_bonsai_func,
        delete_bonsai_func=delete_bonsai_func,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        build_create_bonsai_confirmation=build_create_bonsai_confirmation,
        build_delete_bonsai_confirmation=build_delete_bonsai_confirmation,
        build_update_bonsai_confirmation=build_update_bonsai_confirmation,
        build_create_bonsai_species_selection_question=build_create_bonsai_species_selection_question,
        write_wiki_page_func=write_wiki_page_func,
    )
