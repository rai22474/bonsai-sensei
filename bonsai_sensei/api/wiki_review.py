import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from bonsai_sensei.domain.wiki_review_session import WikiReviewSession
from bonsai_sensei.knowledge_base import wiki_git

router = APIRouter(prefix="/wiki/review", tags=["wiki-review"])


@router.get("/sessions")
def list_review_sessions(request: Request):
    """List all active wiki review sessions."""
    sessions = request.app.state.wiki_review_sessions
    return [_serialize_session(session) for session in sessions.values()]


@router.get("/sessions/{review_id}")
def get_review_session(review_id: str, request: Request):
    """Return the current state of a wiki review session."""
    session = _get_session_or_404(review_id, request)
    return _serialize_session(session)


@router.post("/sessions/{review_id}/pages/{page_index}/confirm", status_code=200)
def confirm_page(review_id: str, page_index: int, request: Request):
    """Mark a page as confirmed (accepted as-is). Removes it from the pending list."""
    session = _get_session_or_404(review_id, request)
    page_path = _get_page_or_404(session, page_index)

    session.resolve_page(page_path, reverted=False)
    _cleanup_if_complete(review_id, session, request)
    return _serialize_session(session)


@router.post("/sessions/{review_id}/pages/{page_index}/revert", status_code=200)
def revert_page(review_id: str, page_index: int, request: Request):
    """Revert a page to its state before the dreamer commit. Removes it from pending."""
    session = _get_session_or_404(review_id, request)
    page_path = _get_page_or_404(session, page_index)
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))

    try:
        wiki_git.revert_page(wiki_root, page_path, session.commit_hash)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"git revert failed: {error}")

    session.resolve_page(page_path, reverted=True)
    _cleanup_if_complete(review_id, session, request)
    return _serialize_session(session)


@router.post("/sessions", status_code=201)
def create_test_review_session(request: Request):
    """Stage and commit all uncommitted wiki changes, then create a review session.

    For use in acceptance tests only. Simulates what the wiki dreamer does after a run
    without invoking the LLM agent.
    """
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    commit_hash = wiki_git.commit_wiki_changes(wiki_root, "test: stage wiki changes for review")
    if not commit_hash:
        raise HTTPException(status_code=422, detail="no_uncommitted_changes")

    changed_files = wiki_git.get_changed_files(wiki_root, commit_hash)
    reviewable = [path for path in changed_files if path.endswith(".md")]
    review_id = uuid.uuid4().hex[:8]
    session = WikiReviewSession(
        review_id=review_id,
        commit_hash=commit_hash,
        pending=reviewable,
    )
    request.app.state.wiki_review_sessions[review_id] = session
    return _serialize_session(session)


def _get_session_or_404(review_id: str, request: Request) -> WikiReviewSession:
    session = request.app.state.wiki_review_sessions.get(review_id)
    if not session:
        raise HTTPException(status_code=404, detail="review_session_not_found")
    return session


def _get_page_or_404(session: WikiReviewSession, page_index: int) -> str:
    if page_index >= len(session.pending):
        raise HTTPException(status_code=404, detail="page_not_found_in_pending")
    return session.pending[page_index]


def _cleanup_if_complete(review_id: str, session: WikiReviewSession, request: Request) -> None:
    if session.is_complete:
        request.app.state.wiki_review_sessions.pop(review_id, None)


def _serialize_session(session: WikiReviewSession) -> dict:
    return {
        "review_id": session.review_id,
        "commit_hash": session.commit_hash,
        "pending": session.pending,
        "confirmed": session.confirmed,
        "reverted": session.reverted,
        "is_complete": session.is_complete,
    }
