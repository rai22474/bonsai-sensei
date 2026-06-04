from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

router = APIRouter(tags=["episodes"])


class Message(BaseModel):
    role: str
    content: str


class AddEpisodeRequest(BaseModel):
    user_id: str
    messages: list[Message]


class MemorySearchResponse(BaseModel):
    memories: list[str]


class ObservationsResponse(BaseModel):
    observations: list[str]


@router.post("/episodes", status_code=202)
async def add_episode(body: AddEpisodeRequest, request: Request, background_tasks: BackgroundTasks):
    """Queue a conversation episode for async Graphiti extraction."""
    messages = [{"role": message.role, "content": message.content} for message in body.messages]
    background_tasks.add_task(request.app.state.store.add_episode, body.user_id, messages)
    return {"status": "accepted"}


@router.get("/memory", response_model=MemorySearchResponse)
async def search_memory(user_id: str, query: str, request: Request):
    """Return relevant facts for a user given a query."""
    facts = await request.app.state.store.search(user_id, query)
    return MemorySearchResponse(memories=facts)


@router.get("/observations", response_model=ObservationsResponse)
async def get_observations(request: Request, since: str | None = None):
    """Return episode content for all users since the given ISO datetime."""
    since_dt = datetime.fromisoformat(since) if since else datetime.min.replace(tzinfo=timezone.utc)
    observations = await request.app.state.store.get_new_episodes(since_dt)
    return ObservationsResponse(observations=observations)
