import os
from collections.abc import Sequence, Mapping
from typing import Any

from google.adk.events.event import Event
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import MemoryEntry, SearchMemoryResponse
from google.adk.sessions.session import Session
from google.genai import types
from mem0 import AsyncMemory

_MEMORY_SYNCED_KEY = "memory_synced_event_count"


class Mem0MemoryService(BaseMemoryService):
    def __init__(self, mem0_client: AsyncMemory):
        self._mem0 = mem0_client

    async def add_session_to_memory(self, session: Session) -> None:
        already_synced = session.state.get(_MEMORY_SYNCED_KEY, 0)
        new_events = session.events[already_synced:]
        messages = _extract_text_messages(new_events)
        if not messages:
            return
        await self._mem0.add(messages, user_id=session.user_id, agent_id="bonsai_sensei")
        session.state[_MEMORY_SYNCED_KEY] = len(session.events)

    async def search_memory(self, *, app_name: str, user_id: str, query: str) -> SearchMemoryResponse:
        results = await self._mem0.search(query, filters={"user_id": user_id}, top_k=10)
        return SearchMemoryResponse(
            memories=[
                MemoryEntry(
                    content=types.Content(parts=[types.Part(text=result["memory"])]),
                    id=result.get("id"),
                    timestamp=result.get("created_at"),
                )
                for result in results.get("results", [])
            ]
        )


def create_mem0_client(database_url: str, history_db_path: str = "/tmp/mem0_history.db") -> AsyncMemory:
    """Creates an AsyncMemory client configured with pgvector backend and Gemini LLM/embedder."""
    config: dict[str, Any] = {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "connection_string": database_url,
                "collection_name": "episodic_memory",
                "embedding_model_dims": 768,
                "hnsw": False,
                "diskann": False,
            },
        },
        "llm": {
            "provider": "gemini",
            "config": {"model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")},
        },
        "embedder": {
            "provider": "gemini",
            "config": {
                "model": "gemini-embedding-001",
                "embedding_dims": 768,
            },
        },
        "history_db_path": history_db_path,
    }
    return AsyncMemory.from_config(config)


def _extract_text_messages(events: Sequence[Event]) -> list[dict]:
    messages = []
    for event in events:
        if not event.content or not event.content.parts:
            continue
        text_parts = [part.text for part in event.content.parts if part.text]
        if not text_parts:
            continue
        role = "user" if event.author == "user" else "assistant"
        messages.append({"role": role, "content": " ".join(text_parts)})
    return messages
