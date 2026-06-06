import pytest
from hamcrest import assert_that, equal_to, contains_string

from knowledge_base.dreamer.read_card import create_read_card_tool


def should_return_card_content(transcripts_root):
    (transcripts_root / "cards" / "benavente" / "abc123.md").write_text("# Ficha\nContenido.")
    read_card = create_read_card_tool(transcripts_root)

    result = read_card("benavente/abc123.md")

    assert_that(result["status"], equal_to("success"))
    assert_that(result["content"], contains_string("# Ficha"))


def should_return_error_when_card_not_found(transcripts_root):
    read_card = create_read_card_tool(transcripts_root)

    result = read_card("benavente/nonexistent.md")

    assert_that(result["status"], equal_to("error"))
    assert_that(result["message"], equal_to("card_not_found"))


def should_return_error_on_path_traversal(transcripts_root):
    read_card = create_read_card_tool(transcripts_root)

    result = read_card("../../etc/passwd")

    assert_that(result["status"], equal_to("error"))
    assert_that(result["message"], equal_to("invalid_path"))


@pytest.fixture
def transcripts_root(tmp_path):
    (tmp_path / "cards" / "benavente").mkdir(parents=True)
    return tmp_path
