import pytest
from hamcrest import assert_that, equal_to, has_item

from knowledge_base.dreamer.list_cards import create_list_cards_tool


def should_list_all_cards_when_no_channel_filter(transcripts_root):
    (transcripts_root / "cards" / "benavente" / "abc123.md").write_text("content")
    (transcripts_root / "cards" / "canaldebonsai" / "xyz789.md").write_text("content")
    list_cards = create_list_cards_tool(transcripts_root)

    result = list_cards()

    assert_that(result["status"], equal_to("success"))
    assert_that(result["cards"], has_item("benavente/abc123.md"))
    assert_that(result["cards"], has_item("canaldebonsai/xyz789.md"))


def should_filter_cards_by_channel(transcripts_root):
    (transcripts_root / "cards" / "benavente" / "abc123.md").write_text("content")
    (transcripts_root / "cards" / "canaldebonsai" / "xyz789.md").write_text("content")
    list_cards = create_list_cards_tool(transcripts_root)

    result = list_cards(channel="benavente")

    assert_that(len(result["cards"]), equal_to(1))
    assert_that(result["cards"][0], equal_to("benavente/abc123.md"))


def should_return_empty_list_for_nonexistent_channel(transcripts_root):
    list_cards = create_list_cards_tool(transcripts_root)

    result = list_cards(channel="nonexistent")

    assert_that(result["cards"], equal_to([]))


def should_return_error_on_path_traversal(transcripts_root):
    list_cards = create_list_cards_tool(transcripts_root)

    result = list_cards(channel="../secret")

    assert_that(result["status"], equal_to("error"))
    assert_that(result["message"], equal_to("invalid_path"))


@pytest.fixture
def transcripts_root(tmp_path):
    (tmp_path / "cards" / "benavente").mkdir(parents=True)
    (tmp_path / "cards" / "canaldebonsai").mkdir(parents=True)
    return tmp_path
