from functools import partial

from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain.services.bonsai.gardener import create_gardener


def create_gardener_group(
    model: object,
    session_factory,
):
    list_bonsai_func = partial(garden.list_bonsai, create_session=session_factory)
    create_bonsai_func = partial(garden.create_bonsai, create_session=session_factory)
    get_bonsai_by_name_func = partial(
        garden.get_bonsai_by_name, create_session=session_factory
    )
    update_bonsai_func = partial(garden.update_bonsai, create_session=session_factory)
    delete_bonsai_func = partial(garden.delete_bonsai, create_session=session_factory)
    list_species_func = partial(herbarium.list_species, create_session=session_factory)
    return create_gardener(
        model=model,
        list_bonsai_func=list_bonsai_func,
        create_bonsai_func=create_bonsai_func,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        update_bonsai_func=update_bonsai_func,
        delete_bonsai_func=delete_bonsai_func,
        list_species_func=list_species_func,
    )
