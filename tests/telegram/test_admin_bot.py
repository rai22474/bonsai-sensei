from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import telegram
from hamcrest import assert_that, calling, equal_to, has_key, not_none, raises

from bonsai_sensei.telegram.admin_bot import AdminBotManager


async def should_notify_admin_when_wiki_changes(manager, bot):
    await manager.notify_wiki_changes(changed_files=["species/ficus.md"], commit_hash="abc123")

    bot.send_wiki_review_notification.assert_awaited_once()
    call_kwargs = bot.send_wiki_review_notification.call_args.kwargs
    assert_that(call_kwargs["chat_id"], equal_to("admin-chat-42"), "Should send to configured chat_id")


async def should_save_review_session_when_notified(manager, wiki_review_sessions):
    await manager.notify_wiki_changes(changed_files=["species/ficus.md"], commit_hash="abc123")

    assert_that(len(wiki_review_sessions), equal_to(1), "Should add one session to the sessions dict")


async def should_persist_sessions_on_notify(manager, tmp_path):
    with patch("bonsai_sensei.telegram.admin_bot.save_review_sessions") as mock_save:
        await manager.notify_wiki_changes(changed_files=["species/ficus.md"], commit_hash="abc123")

        mock_save.assert_called_once()
        assert_that(mock_save.call_args.args[0], equal_to(tmp_path), "Should persist to correct wiki_root")


async def should_not_notify_when_chat_id_not_set(bot, tmp_path):
    wiki_review_sessions = {}
    manager_without_chat_id = AdminBotManager(
        bot=bot,
        wiki_root=tmp_path,
        wiki_review_sessions=wiki_review_sessions,
        run_wiki_dreamer=MagicMock(),
        ingest_transcript=MagicMock(),
        user_message_handler=MagicMock(),
        wiki_review_handler=MagicMock(),
    )

    await manager_without_chat_id.notify_wiki_changes(changed_files=["page.md"], commit_hash="abc")

    bot.send_wiki_review_notification.assert_not_called()
    assert_that(len(wiki_review_sessions), equal_to(0), "Should not create session when no chat_id")


async def should_catch_telegram_error_on_notify(manager, bot):
    bot.send_wiki_review_notification.side_effect = telegram.error.TelegramError("network error")

    await manager.notify_wiki_changes(changed_files=["page.md"], commit_hash="abc")

    assert_that(True, equal_to(True), "TelegramError should not propagate")


async def should_re_notify_all_pending_sessions(manager, bot, wiki_review_sessions):
    from bonsai_sensei.domain.wiki_review_session import WikiReviewSession

    wiki_review_sessions["session1"] = WikiReviewSession(
        review_id="session1", commit_hash="abc", pending=["page1.md"]
    )
    wiki_review_sessions["session2"] = WikiReviewSession(
        review_id="session2", commit_hash="def", pending=["page2.md"]
    )

    await manager.re_notify_pending_sessions()

    assert_that(bot.send_wiki_review_notification.await_count, equal_to(2), "Should notify once per pending session")


async def should_set_chat_id_on_start(manager, tmp_path):
    with patch("bonsai_sensei.telegram.admin_bot.save_admin_chat_id") as mock_save:
        manager.set_chat_id("new-chat-99")

        assert_that(manager.chat_id, equal_to("new-chat-99"), "chat_id property should reflect set value")


@pytest.fixture
def bot():
    mock_bot = MagicMock()
    mock_bot.send_wiki_review_notification = AsyncMock()
    return mock_bot


@pytest.fixture
def wiki_review_sessions():
    return {}


@pytest.fixture
def manager(bot, tmp_path, wiki_review_sessions):
    instance = AdminBotManager(
        bot=bot,
        wiki_root=tmp_path,
        wiki_review_sessions=wiki_review_sessions,
        run_wiki_dreamer=MagicMock(),
        ingest_transcript=MagicMock(),
        user_message_handler=MagicMock(),
        wiki_review_handler=MagicMock(),
    )
    instance.set_chat_id("admin-chat-42")
    return instance
