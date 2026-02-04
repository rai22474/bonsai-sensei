import os
from functools import partial

from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_advisor import (
    create_fertilizer_storekeeper,
)
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_advisor import (
    create_phytosanitary_storekeeper,
)
from bonsai_sensei.domain.services.storekeeper.storekeeper import create_storekeeper
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import (
    create_tavily_searcher,
)


def create_storekeeper_group(
    model: object,
    session_factory,
):
    list_fertilizers_func = partial(
        fertilizer_catalog.list_fertilizers, create_session=session_factory
    )
    create_fertilizer_func = partial(
        fertilizer_catalog.create_fertilizer, create_session=session_factory
    )
    get_fertilizer_by_name_func = partial(
        fertilizer_catalog.get_fertilizer_by_name, create_session=session_factory
    )
    list_phytosanitary_func = partial(
        phytosanitary_registry.list_phytosanitary, create_session=session_factory
    )
    create_phytosanitary_func = partial(
        phytosanitary_registry.create_phytosanitary, create_session=session_factory
    )
    get_phytosanitary_by_name_func = partial(
        phytosanitary_registry.get_phytosanitary_by_name,
        create_session=session_factory,
    )
    tavily_base_url = os.getenv("TAVILY_API_BASE")
    fertilizer_searcher = create_tavily_searcher(os.getenv("TAVILY_API_KEY"), tavily_base_url)
    fertilizer_storekeeper = create_fertilizer_storekeeper(
        model=model,
        create_fertilizer_func=create_fertilizer_func,
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        searcher=fertilizer_searcher,
    )
    phytosanitary_searcher = create_tavily_searcher(os.getenv("TAVILY_API_KEY"), tavily_base_url)
    phytosanitary_storekeeper = create_phytosanitary_storekeeper(
        model=model,
        create_phytosanitary_func=create_phytosanitary_func,
        list_phytosanitary_func=list_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        searcher=phytosanitary_searcher,
    )
    return create_storekeeper(
        model=model,
        fertilizer_storekeeper=fertilizer_storekeeper,
        phytosanitary_storekeeper=phytosanitary_storekeeper,
    )
