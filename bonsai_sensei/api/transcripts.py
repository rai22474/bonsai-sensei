from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

router = APIRouter(prefix="/wiki/transcripts", tags=["transcripts"])


class IngestRequest(BaseModel):
    url: str
    channel: str


@router.post("/ingest", status_code=202)
async def ingest_transcript(body: IngestRequest, request: Request, background_tasks: BackgroundTasks):
    """Trigger the ingestion pipeline for a YouTube video.

    Downloads the transcript, cleans it, extracts a knowledge card, and merges
    non-conflicting information into the wiki. Runs asynchronously in the background.

    Args:
        body: Request body with the YouTube URL and channel slug.
    """
    background_tasks.add_task(request.app.state.ingest_transcript, body.url, body.channel)
    return {"status": "ingesting", "url": body.url, "channel": body.channel}


@router.post("/wiki-keeper/run", status_code=202)
async def run_wiki_keeper(request: Request, background_tasks: BackgroundTasks):
    """Trigger the wiki keeper manually to maintain wiki coherence.

    Reads all knowledge cards and updates or creates topic pages in the main wiki.
    Runs asynchronously in the background.
    """
    background_tasks.add_task(request.app.state.run_wiki_keeper)
    return {"status": "running"}
