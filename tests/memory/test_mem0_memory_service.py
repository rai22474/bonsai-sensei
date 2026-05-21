import pytest
from unittest.mock import AsyncMock, MagicMock
from hamcrest import assert_that, equal_to, has_length, empty

from google.adk.events.event import Event
from google.adk.sessions.session import Session
from google.genai import types

from bonsai_sensei.memory.mem0_memory_service import Mem0MemoryService


async def should_add_text_messages_to_mem0_on_session_ingest(mem0_client, session_with_text):
    service = Mem0MemoryService(mem0_client)
    await service.add_session_to_memory(session_with_text)

    mem0_client.add.assert_called_once_with(
        [
            {"role": "user", "content": "Hanako tiene hojas amarillas"},
            {"role": "assistant", "content": "Puede ser clorosis leve"},
        ],
        user_id="user-123",
        agent_id="bonsai_sensei",
    )


async def should_only_send_new_events_when_some_already_synced(mem0_client, session_with_text):
    session_with_text.state["memory_synced_event_count"] = 1
    service = Mem0MemoryService(mem0_client)
    await service.add_session_to_memory(session_with_text)

    mem0_client.add.assert_called_once_with(
        [{"role": "assistant", "content": "Puede ser clorosis leve"}],
        user_id="user-123",
        agent_id="bonsai_sensei",
    )


async def should_update_synced_count_in_session_state_after_add(mem0_client, session_with_text):
    service = Mem0MemoryService(mem0_client)
    await service.add_session_to_memory(session_with_text)

    assert_that(
        session_with_text.state["memory_synced_event_count"],
        equal_to(2),
        "synced count should equal total number of session events after add",
    )


async def should_skip_add_when_session_has_no_text_events(mem0_client, session_no_text):
    service = Mem0MemoryService(mem0_client)
    await service.add_session_to_memory(session_no_text)

    mem0_client.add.assert_not_called()


async def should_skip_tool_call_only_events(mem0_client):
    session = Session(
        id="s1",
        app_name="bonsai_sensei",
        user_id="user-123",
        events=[
            Event(
                id="e1",
                author="user",
                content=types.Content(parts=[types.Part(text="registra una observacion")]),
                invocation_id="inv-1",
            ),
            Event(
                id="e2",
                author="sensei",
                content=types.Content(
                    parts=[types.Part(function_call=types.FunctionCall(name="record_observation", args={}))]
                ),
                invocation_id="inv-1",
            ),
            Event(
                id="e3",
                author="sensei",
                content=types.Content(parts=[types.Part(text="Observacion registrada")]),
                invocation_id="inv-1",
            ),
        ],
    )
    service = Mem0MemoryService(mem0_client)
    await service.add_session_to_memory(session)

    mem0_client.add.assert_called_once_with(
        [
            {"role": "user", "content": "registra una observacion"},
            {"role": "assistant", "content": "Observacion registrada"},
        ],
        user_id="user-123",
        agent_id="bonsai_sensei",
    )


async def should_return_search_results_as_memory_entries(mem0_client):
    mem0_client.search.return_value = {
        "results": [
            {
                "memory": "Hanako tiene clorosis leve en el apice",
                "id": "mem-abc",
                "created_at": "2026-05-18T10:00:00",
            },
            {
                "memory": "Se aplico fertilizante nitrogenado en primavera",
                "id": "mem-def",
                "created_at": "2026-05-10T09:00:00",
            },
        ]
    }
    service = Mem0MemoryService(mem0_client)
    response = await service.search_memory(
        app_name="bonsai_sensei", user_id="user-123", query="clorosis Hanako"
    )

    assert_that(response.memories, has_length(2), "should return all results as MemoryEntry objects")
    assert_that(
        response.memories[0].content.parts[0].text,
        equal_to("Hanako tiene clorosis leve en el apice"),
    )
    assert_that(response.memories[0].id, equal_to("mem-abc"))
    assert_that(response.memories[0].timestamp, equal_to("2026-05-18T10:00:00"))


async def should_return_empty_response_when_no_memories_found(mem0_client):
    mem0_client.search.return_value = {"results": []}
    service = Mem0MemoryService(mem0_client)
    response = await service.search_memory(
        app_name="bonsai_sensei", user_id="user-123", query="algo inexistente"
    )

    assert_that(response.memories, empty(), "should return empty list when no memories found")


async def should_pass_user_id_filter_to_mem0_search(mem0_client):
    mem0_client.search.return_value = {"results": []}
    service = Mem0MemoryService(mem0_client)
    await service.search_memory(app_name="bonsai_sensei", user_id="user-456", query="riego")

    mem0_client.search.assert_called_once_with(
        "riego", filters={"user_id": "user-456"}, top_k=10
    )


@pytest.fixture
def mem0_client():
    client = MagicMock()
    client.add = AsyncMock()
    client.search = AsyncMock(return_value={"results": []})
    return client


@pytest.fixture
def session_with_text():
    return Session(
        id="session-1",
        app_name="bonsai_sensei",
        user_id="user-123",
        events=[
            Event(
                id="e1",
                author="user",
                content=types.Content(parts=[types.Part(text="Hanako tiene hojas amarillas")]),
                invocation_id="inv-1",
            ),
            Event(
                id="e2",
                author="sensei",
                content=types.Content(parts=[types.Part(text="Puede ser clorosis leve")]),
                invocation_id="inv-1",
            ),
        ],
    )


@pytest.fixture
def session_no_text():
    return Session(
        id="session-2",
        app_name="bonsai_sensei",
        user_id="user-123",
        events=[
            Event(
                id="e1",
                author="sensei",
                content=types.Content(
                    parts=[types.Part(function_call=types.FunctionCall(name="list_bonsai", args={}))]
                ),
                invocation_id="inv-2",
            ),
        ],
    )
