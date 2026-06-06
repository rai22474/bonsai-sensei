import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from hamcrest import assert_that, equal_to

from knowledge_base.telegram.handle_admin_ingest import handle_admin_ingest


async def should_use_fetch_channel_slug_when_no_channel_in_message(ingest_transcript, fetch_channel_slug):
    fetch_channel_slug.return_value = "davidbenaventebonsai"
    update = _make_update("https://www.youtube.com/watch?v=EJ-_VMTn1t8")

    await handle_admin_ingest(update, MagicMock(), ingest_transcript, fetch_channel_slug)

    fetch_channel_slug.assert_called_once_with("EJ-_VMTn1t8")


async def should_pass_resolved_channel_to_ingest(ingest_transcript, fetch_channel_slug):
    fetch_channel_slug.return_value = "davidbenaventebonsai"
    update = _make_update("https://www.youtube.com/watch?v=EJ-_VMTn1t8")

    await handle_admin_ingest(update, MagicMock(), ingest_transcript, fetch_channel_slug)
    await asyncio.sleep(0)

    assert_that(ingest_transcript.call_args.args[1], equal_to("davidbenaventebonsai"))


async def should_skip_fetch_when_channel_provided_in_message(ingest_transcript, fetch_channel_slug):
    update = _make_update("https://www.youtube.com/watch?v=EJ-_VMTn1t8 benavente")

    await handle_admin_ingest(update, MagicMock(), ingest_transcript, fetch_channel_slug)

    fetch_channel_slug.assert_not_called()


async def should_use_manual_channel_when_provided(ingest_transcript, fetch_channel_slug):
    update = _make_update("https://www.youtube.com/watch?v=EJ-_VMTn1t8 benavente")

    await handle_admin_ingest(update, MagicMock(), ingest_transcript, fetch_channel_slug)
    await asyncio.sleep(0)

    assert_that(ingest_transcript.call_args.args[1], equal_to("benavente"))


async def should_reply_error_on_invalid_url(ingest_transcript, fetch_channel_slug):
    update = _make_update("https://not-a-youtube-url.com/whatever")

    await handle_admin_ingest(update, MagicMock(), ingest_transcript, fetch_channel_slug)

    reply_text = update.message.reply_text.call_args.args[0]
    assert_that("❌" in reply_text, equal_to(True), "Should reply with error on invalid URL")


def _make_update(text: str) -> MagicMock:
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def ingest_transcript():
    mock = AsyncMock()
    return mock


@pytest.fixture
def fetch_channel_slug():
    return MagicMock(return_value="general")
