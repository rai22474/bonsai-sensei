import pytest
from hamcrest import assert_that, equal_to, contains_string

from knowledge_base.wiki_editor.tools.write_page import write_wiki_page


def test_should_create_new_page(tmp_path):
    write_wiki_page("techniques/wiring.md", "# Wiring", tmp_path)

    written = tmp_path / "techniques" / "wiring.md"
    assert_that(written.read_text(encoding="utf-8"), equal_to("# Wiring"), "Should create file with exact content")


def test_should_create_parent_directories(tmp_path):
    write_wiki_page("a/b/c/deep.md", "# Deep", tmp_path)

    assert (tmp_path / "a" / "b" / "c" / "deep.md").exists(), "Should create all parent directories"


def test_should_overwrite_existing_page(tmp_path):
    page = tmp_path / "page.md"
    page.write_text("# Original", encoding="utf-8")

    write_wiki_page("page.md", "# Updated", tmp_path)

    assert_that(page.read_text(encoding="utf-8"), equal_to("# Updated"), "Should overwrite existing content")


def test_should_return_confirmation(tmp_path):
    result = write_wiki_page("page.md", "# Content", tmp_path)

    assert_that(result, contains_string("page.md"), "Confirmation should mention the page path")


def test_should_reject_path_traversal(tmp_path):
    result = write_wiki_page("../../etc/evil.md", "# Evil", tmp_path)

    assert_that(result, contains_string("Error"), "Should reject path traversal attempt")
    assert not (tmp_path.parent.parent / "etc" / "evil.md").exists(), "Should not write outside wiki root"
