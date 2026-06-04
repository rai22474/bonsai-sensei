from collections.abc import Sequence

import httpx
from google.adk.events.event import Event
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import MemoryEntry, SearchMemoryResponse
from google.adk.sessions.session import Session
from google.genai import types

_MEMORY_SYNCED_KEY = "memory_synced_event_count"


class EpisodicMemoryService(BaseMemoryService):
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    async def add_session_to_memory(self, session: Session) -> None:
        already_synced = session.state.get(_MEMORY_SYNCED_KEY, 0)
        new_events = session.events[already_synced:]
        messages = _extract_text_messages(new_events)
        if not messages:
            return
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._base_url}/episodes",
                json={"user_id": session.user_id, "messages": messages},
                timeout=30,
            )
        session.state[_MEMORY_SYNCED_KEY] = len(session.events)

    async def search_memory(self, *, app_name: str, user_id: str, query: str) -> SearchMemoryResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/memory",
                params={"user_id": user_id, "query": query},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        return SearchMemoryResponse(
            memories=[
                MemoryEntry(content=types.Content(parts=[types.Part(text=fact)]))
                for fact in data.get("memories", [])
            ]
        )


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
