from honcho import Honcho
from honcho.api_types import MessageCreateParams
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import MemoryEntry, SearchMemoryResponse
from google.adk.sessions.session import Session
import google.genai.types as types

_AGENT_PEER_ID = "bonsai_sensei"


class HonchoMemoryService(BaseMemoryService):
    def __init__(self, client: Honcho):
        self._client = client

    async def add_session_to_memory(self, session: Session) -> None:
        honcho_session = await self._client.aio.session(session.id)

        all_parts = [
            (session.user_id if event.content.role == "user" else _AGENT_PEER_ID, part.text)
            for event in session.events
            if hasattr(event, "content") and event.content
            for part in event.content.parts
            if part.text
        ]

        existing_page = await honcho_session.aio.messages(size=1)
        already_synced = existing_page.total or 0
        new_parts = all_parts[already_synced:]

        for peer_id, text in new_parts:
            await honcho_session.aio.add_messages([
                MessageCreateParams(peer_id=peer_id, content=text)
            ])

        if new_parts:
            await self._client.aio.schedule_dream(
                observer=session.user_id,
                session=session.id,
            )

    async def search_memory(self, *, app_name: str, user_id: str, query: str) -> SearchMemoryResponse:
        user_peer = await self._client.aio.peer(user_id)
        conclusions_page = await user_peer.conclusions.aio.list()
        entries = [
            MemoryEntry(content=types.Content(parts=[types.Part(text=conclusion.content)]))
            for conclusion in conclusions_page.items
            if conclusion.content
        ]
        return SearchMemoryResponse(memories=entries)


def create_honcho_client(api_key: str, workspace_id: str, base_url: str | None = None) -> Honcho:
    """Create a Honcho client with the given workspace."""
    return Honcho(api_key=api_key, workspace_id=workspace_id, base_url=base_url)
