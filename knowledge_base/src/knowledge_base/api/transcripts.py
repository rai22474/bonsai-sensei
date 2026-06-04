import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

from knowledge_base.dreamer.memory_reader import append_local_observation, update_high_watermark, reset_processed_sessions

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


class ObservationRequest(BaseModel):
    text: str


@router.post("/observations", status_code=200)
def submit_local_observation(body: ObservationRequest):
    """Submit a local observation for the dreamer to process on its next run.

    Used in acceptance tests to inject observations without a Honcho connection.
    """
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    append_local_observation(wiki_root, body.text)
    return {"status": "queued", "text": body.text}


@router.post("/wiki-dreamer/watermark/reset", status_code=200)
def reset_wiki_dreamer_watermark():
    """Advance the episodic memory watermark to the current time.

    For use in acceptance tests to ensure the next dreamer run only processes
    observations created after this call, ignoring observations from prior test runs.
    """
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    update_high_watermark(wiki_root)
    reset_processed_sessions(wiki_root)
    return {"status": "reset"}


class CardRequest(BaseModel):
    path: str
    content: str


@router.post("/cards", status_code=200)
def create_knowledge_card(body: CardRequest):
    """Write a knowledge card file for acceptance tests.

    Creates a card at transcripts/cards/{path} so the dreamer can pick it up
    on the next run. The watermark must be reset before this call for the card
    to be treated as new.
    """
    transcripts_root = Path(os.getenv("TRANSCRIPTS_PATH", "./transcripts"))
    card_path = transcripts_root / "cards" / body.path
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(body.content, encoding="utf-8")
    return {"status": "created", "path": str(card_path.relative_to(transcripts_root / "cards"))}


@router.delete("/cards", status_code=200)
def delete_knowledge_card(path: str):
    """Delete a knowledge card file. Used in acceptance test teardown."""
    transcripts_root = Path(os.getenv("TRANSCRIPTS_PATH", "./transcripts"))
    card_path = transcripts_root / "cards" / path
    if card_path.exists():
        card_path.unlink()
    return {"status": "deleted", "path": path}


@router.get("/wiki-dreamer/wikilinks/tracker", status_code=200)
def get_wikilink_tracker():
    """Return the current wikilink processed tracker. Used in acceptance tests."""
    import json
    from knowledge_base.dreamer.runner import _PROCESSED_WIKILINKS_FILE
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    tracker_file = wiki_root / _PROCESSED_WIKILINKS_FILE
    if not tracker_file.exists():
        return {}
    return json.loads(tracker_file.read_text())


@router.post("/wiki-dreamer/wikilinks/reset", status_code=200)
def reset_wikilink_tracker():
    """Clear the wikilink processed tracker. Used in acceptance tests."""
    from knowledge_base.dreamer.runner import _PROCESSED_WIKILINKS_FILE
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    tracker = wiki_root / _PROCESSED_WIKILINKS_FILE
    tracker.unlink(missing_ok=True)
    return {"status": "reset"}


@router.delete("/wiki-dreamer/wikilinks/pages", status_code=200)
def remove_page_from_wikilink_tracker(path: str):
    """Remove a single page from the wikilink tracker so it gets re-processed."""
    import json
    from knowledge_base.dreamer.runner import _PROCESSED_WIKILINKS_FILE
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    tracker_file = wiki_root / _PROCESSED_WIKILINKS_FILE
    if not tracker_file.exists():
        return {"status": "not_found"}
    data = json.loads(tracker_file.read_text())
    data.pop(path, None)
    tracker_file.write_text(json.dumps(data))
    return {"status": "removed", "path": path}


@router.post("/wiki-dreamer/wikilinks/pages", status_code=200)
def mark_page_as_wikilink_processed(path: str):
    """Mark a page as already processed for wikilinks (using current mtime). Used in acceptance tests."""
    import json
    from knowledge_base.dreamer.runner import _PROCESSED_WIKILINKS_FILE
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    tracker_file = wiki_root / _PROCESSED_WIKILINKS_FILE
    data = json.loads(tracker_file.read_text()) if tracker_file.exists() else {}
    page = wiki_root / path
    data[path] = page.stat().st_mtime if page.exists() else 0.0
    tracker_file.write_text(json.dumps(data))
    return {"status": "marked", "path": path}


class WikiEditorRequest(BaseModel):
    chat_id: str
    text: str


@router.post("/wiki-editor/run/sync", status_code=200)
async def run_wiki_editor_sync(body: WikiEditorRequest, request: Request):
    """Run the wiki editor synchronously with a given text. Used in acceptance tests."""
    response = await request.app.state.wiki_editor(body.chat_id, body.text)
    return {"status": "completed", "response": response}
