import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

from bonsai_sensei.knowledge_base.dreamer.memory_reader import update_high_watermark

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


@router.post("/wiki-dreamer/run", status_code=202)
async def run_wiki_dreamer(request: Request, background_tasks: BackgroundTasks):
    """Trigger the wiki dreamer manually to maintain wiki coherence.

    Reads all knowledge cards and updates or creates topic pages in the main wiki.
    Runs asynchronously in the background.
    """
    background_tasks.add_task(request.app.state.run_wiki_dreamer)
    return {"status": "running"}


@router.post("/wiki-dreamer/run/sync", status_code=200)
async def run_wiki_dreamer_sync(request: Request):
    """Trigger the wiki dreamer synchronously and wait for completion.

    For use in acceptance tests where the caller must wait for the dreamer to finish
    before asserting on wiki state.
    """
    await request.app.state.run_wiki_dreamer()
    return {"status": "completed"}


@router.post("/wiki-dreamer/watermark/reset", status_code=200)
def reset_wiki_dreamer_watermark():
    """Advance the episodic memory watermark to the current time.

    For use in acceptance tests to ensure the next dreamer run only processes
    observations created after this call, ignoring observations from prior test runs.
    """
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    update_high_watermark(wiki_root)
    return {"status": "reset"}
