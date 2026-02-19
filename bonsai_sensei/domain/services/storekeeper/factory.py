import os
from functools import partial

from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_storekeeper import (
    create_fertilizer_storekeeper,
)
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_storekeeper import (
    create_phytosanitary_storekeeper,
)
from bonsai_sensei.domain.services.storekeeper.storekeeper import create_storekeeper
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import (
    create_tavily_searcher,
)
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore


def create_storekeeper_group(
    model: object,
    session_factory,
    confirmation_registry: dict[str, Confirmation] | None = None,
    confirmation_store: ConfirmationStore | None = None,
):
    list_fertilizers_func = partial(
        fertilizer_catalog.list_fertilizers, create_session=session_factory
    )
    get_fertilizer_by_name_func = partial(
        fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory
    )
    list_phytosanitary_func = partial(
        phytosanitary_registry.list_phytosanitary, create_session=session_factory
    )
    get_phytosanitary_by_name_func = partial(
        phytosanitary_registry.get_phytosanitary_by_name,
        create_session=session_factory,
    )
    
    tavily_base_url = os.getenv("TAVILY_API_BASE")
    fertilizer_searcher = create_tavily_searcher(
        os.getenv("TAVILY_API_KEY"), tavily_base_url
    )
    fertilizer_storekeeper = create_fertilizer_storekeeper(
        model=model,
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        searcher=fertilizer_searcher,
        confirmation_store=confirmation_store,
        create_tool=partial(
            fertilizer_catalog.create_fertilizer, create_session=session_factory
        ),
        update_tool=partial(
            fertilizer_catalog.update_fertilizer, create_session=session_factory
        ),
        delete_tool=partial(
            fertilizer_catalog.delete_fertilizer, create_session=session_factory
        ),
    )
    phytosanitary_searcher = create_tavily_searcher(
        os.getenv("TAVILY_API_KEY"), tavily_base_url
    )
    phytosanitary_storekeeper = create_phytosanitary_storekeeper(
        model=model,
        list_phytosanitary_func=list_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        searcher=phytosanitary_searcher,
        confirmation_store=confirmation_store,
        create_tool=partial(
            phytosanitary_registry.create_phytosanitary, create_session=session_factory
        ),
        update_tool=partial(
            phytosanitary_registry.update_phytosanitary, create_session=session_factory
        ),
        delete_tool=partial(
            phytosanitary_registry.delete_phytosanitary, create_session=session_factory
        ),
    )
    return create_storekeeper(
        model=model,
        fertilizer_storekeeper=fertilizer_storekeeper,
        phytosanitary_storekeeper=phytosanitary_storekeeper,
    )
