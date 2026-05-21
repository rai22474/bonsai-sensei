from functools import partial
from typing import Callable

from bonsai_sensei.domain.services.cultivation.factory import create_cultivation_group
from bonsai_sensei.domain.services.garden.factory import create_gardener_group
from bonsai_sensei.domain.services.storekeeper.factory import create_storekeeper_group
from bonsai_sensei.domain.services.factory import create_agents, create_sensei_group


def create_sensei_agent(
    model: object,
    session_factory,
    orchestrator_model: object,
    wiki_root: str,
    pending_photos: dict,
    ask_confirmation: Callable,
    ask_human: Callable,
    ask_selection: Callable,
    ask_plan_review: Callable,
    cultivation_messages: dict,
    garden_messages: dict,
    storekeeper_messages: dict,
    botanist_messages: dict,
    ask_poll: Callable | None = None,
    searcher: Callable | None = None,
):
    cultivation_group_factory = partial(
        create_cultivation_group,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_human=ask_human,
        ask_selection=ask_selection,
        ask_plan_review=ask_plan_review,
        ask_poll=ask_poll,
        orchestrator_model=orchestrator_model,
        searcher=searcher,
        **cultivation_messages,
        **botanist_messages,
    )
    gardener_group_factory = partial(
        create_gardener_group,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        ask_selection=ask_selection,
        pending_photos=pending_photos,
        **garden_messages,
    )
    storekeeper_group_factory = partial(
        create_storekeeper_group,
        session_factory=session_factory,
        ask_confirmation=ask_confirmation,
        **storekeeper_messages,
    )
    sensei_group_factory = partial(
        create_sensei_group,
        session_factory=session_factory,
        orchestrator_model=orchestrator_model,
        wiki_root=wiki_root,
    )
    return create_agents(
        model=model,
        create_cultivation_group=cultivation_group_factory,
        create_gardener_group=gardener_group_factory,
        create_storekeeper_group=storekeeper_group_factory,
        create_sensei_group=sensei_group_factory,
    )
