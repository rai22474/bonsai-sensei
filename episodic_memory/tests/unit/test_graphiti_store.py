from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hamcrest import assert_that, equal_to, has_length

from episodic_memory.graphiti_store import GraphitiStore


async def should_add_episode_formats_messages_as_role_content():
    graphiti = MagicMock()
    graphiti.add_episode = AsyncMock()
    store = GraphitiStore(graphiti)

    await store.add_episode("user-1", [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "hola, ¿en qué puedo ayudarte?"},
    ])

    call_kwargs = graphiti.add_episode.call_args.kwargs
    assert_that(call_kwargs["episode_body"], equal_to("user: hola\nassistant: hola, ¿en qué puedo ayudarte?"))
    assert_that(call_kwargs["group_id"], equal_to("user-1"))


async def should_search_returns_facts_for_user():
    graphiti = MagicMock()
    edge1 = MagicMock()
    edge1.fact = "Tanaka tiene hojas amarillas"
    edge2 = MagicMock()
    edge2.fact = None
    graphiti.search = AsyncMock(return_value=[edge1, edge2])
    store = GraphitiStore(graphiti)

    facts = await store.search("user-1", "hojas amarillas")

    graphiti.search.assert_awaited_once_with("hojas amarillas", group_ids=["user-1"])
    assert_that(facts, equal_to(["Tanaka tiene hojas amarillas"]), "Should exclude edges with no fact")


async def should_get_new_episodes_filters_by_valid_at():
    graphiti = MagicMock()
    since = datetime(2024, 6, 1, tzinfo=timezone.utc)

    old_episode = MagicMock()
    old_episode.content = "old content"
    old_episode.valid_at = datetime(2024, 5, 1, tzinfo=timezone.utc)

    new_episode = MagicMock()
    new_episode.content = "new content"
    new_episode.valid_at = datetime(2024, 7, 1, tzinfo=timezone.utc)

    empty_episode = MagicMock()
    empty_episode.content = ""
    empty_episode.valid_at = datetime(2024, 7, 2, tzinfo=timezone.utc)

    graphiti.retrieve_episodes = AsyncMock(return_value=[old_episode, new_episode, empty_episode])
    store = GraphitiStore(graphiti)

    observations = await store.get_new_episodes(since)

    assert_that(observations, equal_to(["new content"]), "Should include only new non-empty episodes")


@pytest.fixture
def store():
    graphiti = MagicMock()
    graphiti.add_episode = AsyncMock()
    graphiti.search = AsyncMock(return_value=[])
    graphiti.retrieve_episodes = AsyncMock(return_value=[])
    graphiti.build_indices_and_constraints = AsyncMock()
    graphiti.close = AsyncMock()
    return GraphitiStore(graphiti)
