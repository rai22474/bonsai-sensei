from unittest.mock import MagicMock

import pytest
from hamcrest import assert_that, equal_to

from knowledge_base.ingestion.transcript_loader import create_channel_slug_fetcher


def should_extract_handle_from_author_url(http_client):
    fetch = create_channel_slug_fetcher(http_client)
    http_client.get.return_value.json.return_value = {
        "author_url": "https://www.youtube.com/@DavidBenaventeBonsai",
        "author_name": "David Benavente",
    }

    result = fetch("EJ-_VMTn1t8")

    assert_that(result, equal_to("davidbenaventebonsai"))


def should_lowercase_handle(http_client):
    fetch = create_channel_slug_fetcher(http_client)
    http_client.get.return_value.json.return_value = {
        "author_url": "https://www.youtube.com/@MixedCaseHandle",
        "author_name": "Mixed Case",
    }

    result = fetch("some_video_id")

    assert_that(result, equal_to("mixedcasehandle"))


def should_fallback_to_slugified_author_name_when_no_handle(http_client):
    fetch = create_channel_slug_fetcher(http_client)
    http_client.get.return_value.json.return_value = {
        "author_url": "https://www.youtube.com/channel/UCxxxxxx",
        "author_name": "David Benavente",
    }

    result = fetch("some_video_id")

    assert_that(result, equal_to("david_benavente"))


def should_strip_accents_in_author_name_slug(http_client):
    fetch = create_channel_slug_fetcher(http_client)
    http_client.get.return_value.json.return_value = {
        "author_url": "https://www.youtube.com/channel/UCxxxxxx",
        "author_name": "Bonsái España",
    }

    result = fetch("some_video_id")

    assert_that(result, equal_to("bonsai_espana"))


def should_return_general_on_http_error(http_client):
    fetch = create_channel_slug_fetcher(http_client)
    http_client.get.side_effect = Exception("connection refused")

    result = fetch("some_video_id")

    assert_that(result, equal_to("general"))


def should_return_general_on_http_error_status(http_client):
    fetch = create_channel_slug_fetcher(http_client)
    http_client.get.return_value.raise_for_status.side_effect = Exception("404")

    result = fetch("some_video_id")

    assert_that(result, equal_to("general"))


@pytest.fixture
def http_client():
    mock = MagicMock()
    mock.get.return_value.raise_for_status = MagicMock()
    return mock
