import pytest
from hamcrest import assert_that, contains_string

from knowledge_base.wiki_editor.tools.read_page import read_wiki_page


def test_should_return_page_content(tmp_path):
    page = tmp_path / "species" / "ficus.md"
    page.parent.mkdir(parents=True)
    page.write_text("# Ficus Retusa", encoding="utf-8")

    result = read_wiki_page("species/ficus.md", tmp_path)

    assert_that(result, contains_string("# Ficus Retusa"), "Should return content of existing page")


def test_should_return_error_when_page_not_found(tmp_path):
    result = read_wiki_page("missing/page.md", tmp_path)

    assert_that(result, contains_string("Error"), "Should return error for missing page")


def test_should_reject_path_traversal(tmp_path):
    result = read_wiki_page("../../etc/passwd", tmp_path)

    assert_that(result, contains_string("Error"), "Should reject path traversal attempt")


@pytest.fixture
def wiki_with_page(tmp_path):
    page = tmp_path / "test.md"
    page.write_text("# Test", encoding="utf-8")
    return tmp_path
