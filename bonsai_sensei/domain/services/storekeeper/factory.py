import os
from functools import partial
from typing import Callable

from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain.services.storekeeper.storekeeper import create_storekeeper
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import (
    create_tavily_searcher,
)


def create_storekeeper_group(
    model: object,
    session_factory,
    ask_confirmation: Callable,
    build_create_fertilizer_confirmation: Callable,
    build_delete_fertilizer_confirmation: Callable,
    build_update_fertilizer_confirmation: Callable,
    build_create_phytosanitary_confirmation: Callable,
    build_delete_phytosanitary_confirmation: Callable,
    build_update_phytosanitary_confirmation: Callable,
):
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    tavily_base_url = os.getenv("TAVILY_API_BASE")

    return create_storekeeper(
        model=model,
        list_fertilizers_func=partial(
            fertilizer_catalog.list_fertilizers, create_session=session_factory
        ),
        get_fertilizer_by_name_func=partial(
            fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory
        ),
        fertilizer_searcher=create_tavily_searcher(tavily_api_key, tavily_base_url),
        create_fertilizer_func=partial(
            fertilizer_catalog.create_fertilizer, create_session=session_factory
        ),
        update_fertilizer_func=partial(
            fertilizer_catalog.update_fertilizer, create_session=session_factory
        ),
        delete_fertilizer_func=partial(
            fertilizer_catalog.delete_fertilizer, create_session=session_factory
        ),
        list_phytosanitary_func=partial(
            phytosanitary_registry.list_phytosanitary, create_session=session_factory
        ),
        get_phytosanitary_by_name_func=partial(
            phytosanitary_registry.get_phytosanitary_by_name, create_session=session_factory
        ),
        phytosanitary_searcher=create_tavily_searcher(tavily_api_key, tavily_base_url),
        create_phytosanitary_func=partial(
            phytosanitary_registry.create_phytosanitary, create_session=session_factory
        ),
        update_phytosanitary_func=partial(
            phytosanitary_registry.update_phytosanitary, create_session=session_factory
        ),
        delete_phytosanitary_func=partial(
            phytosanitary_registry.delete_phytosanitary, create_session=session_factory
        ),
        ask_confirmation=ask_confirmation,
        build_create_fertilizer_confirmation=build_create_fertilizer_confirmation,
        build_delete_fertilizer_confirmation=build_delete_fertilizer_confirmation,
        build_update_fertilizer_confirmation=build_update_fertilizer_confirmation,
        build_create_phytosanitary_confirmation=build_create_phytosanitary_confirmation,
        build_delete_phytosanitary_confirmation=build_delete_phytosanitary_confirmation,
        build_update_phytosanitary_confirmation=build_update_phytosanitary_confirmation,
    )
