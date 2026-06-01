from unittest.mock import AsyncMock, MagicMock

import pytest
from hamcrest import assert_that, equal_to, empty

from knowledge_base.wiki_review_session import WikiReviewSession
from knowledge_base.telegram.handle_wiki_review_callback import handle_wiki_review_callback


async def should_call_send_page_diff_message_when_page_selected(review_session, wiki_review_sessions, send_page_diff_message, send_review_status, wiki_root):
    update = _make_update(f"wiki:select:{review_session.review_id}:0")

    await handle_wiki_review_callback(
        update=update,
        context=MagicMock(),
        wiki_review_sessions=wiki_review_sessions,
        send_page_diff_message=send_page_diff_message,
        send_review_status=send_review_status,
        wiki_root=str(wiki_root),
        admin_chat_id="admin_chat",
    )

    send_page_diff_message.assert_awaited_once()
    call_args = send_page_diff_message.call_args
    assert_that(call_args.args[1], equal_to("bonsai/goku/index.md"),
        "Should send diff for the selected page")


async def should_confirm_page_and_remove_from_pending(review_session, wiki_review_sessions, send_page_diff_message, send_review_status, wiki_root):
    update = _make_update(f"wiki:confirm:{review_session.review_id}:0")

    await handle_wiki_review_callback(
        update=update,
        context=MagicMock(),
        wiki_review_sessions=wiki_review_sessions,
        send_page_diff_message=send_page_diff_message,
        send_review_status=send_review_status,
        wiki_root=str(wiki_root),
        admin_chat_id="admin_chat",
    )

    assert_that(review_session.confirmed, equal_to(["bonsai/goku/index.md"]),
        "Confirmed page should move to confirmed list")
    assert_that("bonsai/goku/index.md" in review_session.pending, equal_to(False),
        "Confirmed page should be removed from pending")


async def should_send_review_status_after_confirm(review_session, wiki_review_sessions, send_page_diff_message, send_review_status, wiki_root):
    update = _make_update(f"wiki:confirm:{review_session.review_id}:0")

    await handle_wiki_review_callback(
        update=update,
        context=MagicMock(),
        wiki_review_sessions=wiki_review_sessions,
        send_page_diff_message=send_page_diff_message,
        send_review_status=send_review_status,
        wiki_root=str(wiki_root),
        admin_chat_id="admin_chat",
    )

    send_review_status.assert_awaited_once()


async def should_remove_session_when_last_page_confirmed(wiki_review_sessions, send_page_diff_message, send_review_status, wiki_root):
    session = WikiReviewSession(review_id="xyz123", commit_hash="abc", pending=["only_page.md"])
    wiki_review_sessions["xyz123"] = session
    update = _make_update("wiki:confirm:xyz123:0")

    await handle_wiki_review_callback(
        update=update,
        context=MagicMock(),
        wiki_review_sessions=wiki_review_sessions,
        send_page_diff_message=send_page_diff_message,
        send_review_status=send_review_status,
        wiki_root=str(wiki_root),
        admin_chat_id="admin_chat",
    )

    assert_that("xyz123" in wiki_review_sessions, equal_to(False),
        "Completed session should be removed from review sessions dict")


async def should_do_nothing_when_session_not_found(wiki_review_sessions, send_page_diff_message, send_review_status, wiki_root):
    update = _make_update("wiki:confirm:nonexistent:0")

    await handle_wiki_review_callback(
        update=update,
        context=MagicMock(),
        wiki_review_sessions=wiki_review_sessions,
        send_page_diff_message=send_page_diff_message,
        send_review_status=send_review_status,
        wiki_root=str(wiki_root),
        admin_chat_id="admin_chat",
    )

    send_page_diff_message.assert_not_called()
    send_review_status.assert_not_called()


def _make_update(callback_data: str) -> MagicMock:
    query = MagicMock()
    query.data = callback_data
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.edit_message_reply_markup = AsyncMock()
    query.message.chat_id = "admin_chat"

    update = MagicMock()
    update.callback_query = query
    return update


@pytest.fixture
def wiki_root(tmp_path):
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=tmp_path,
        capture_output=True,
    )
    return tmp_path


@pytest.fixture
def review_session():
    return WikiReviewSession(
        review_id="test001",
        commit_hash="HEAD",
        pending=["bonsai/goku/index.md", "species/ficus.md"],
    )


@pytest.fixture
def wiki_review_sessions(review_session):
    return {review_session.review_id: review_session}


@pytest.fixture
def send_page_diff_message():
    return AsyncMock()


@pytest.fixture
def send_review_status():
    return AsyncMock()
