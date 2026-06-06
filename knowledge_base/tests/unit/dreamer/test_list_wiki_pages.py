import pytest
from hamcrest import assert_that, equal_to, has_item

from knowledge_base.dreamer.list_wiki_pages import create_list_wiki_pages_tool


def should_list_all_pages_when_no_directory_filter(wiki_root):
    (wiki_root / "species" / "pinus-thunbergii.md").write_text("content")
    (wiki_root / "techniques" / "poda.md").write_text("content")
    list_pages = create_list_wiki_pages_tool(wiki_root)

    result = list_pages()

    assert_that(result["status"], equal_to("success"))
    assert_that(result["pages"], has_item("species/pinus-thunbergii.md"))
    assert_that(result["pages"], has_item("techniques/poda.md"))


def should_filter_pages_by_directory(wiki_root):
    (wiki_root / "species" / "pinus-thunbergii.md").write_text("content")
    (wiki_root / "techniques" / "poda.md").write_text("content")
    list_pages = create_list_wiki_pages_tool(wiki_root)

    result = list_pages(directory="species")

    assert_that(len(result["pages"]), equal_to(1))
    assert_that(result["pages"][0], equal_to("species/pinus-thunbergii.md"))


def should_return_empty_list_for_empty_directory(wiki_root):
    list_pages = create_list_wiki_pages_tool(wiki_root)

    result = list_pages(directory="species")

    assert_that(result["pages"], equal_to([]))


def should_return_error_on_path_traversal(wiki_root):
    list_pages = create_list_wiki_pages_tool(wiki_root)

    result = list_pages(directory="../secret")

    assert_that(result["status"], equal_to("error"))
    assert_that(result["message"], equal_to("invalid_path"))


@pytest.fixture
def wiki_root(tmp_path):
    (tmp_path / "species").mkdir()
    (tmp_path / "techniques").mkdir()
    return tmp_path
