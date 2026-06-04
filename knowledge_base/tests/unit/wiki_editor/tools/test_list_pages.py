from hamcrest import assert_that, contains_string, not_

from knowledge_base.wiki_editor.tools.list_pages import list_wiki_pages


def test_should_list_markdown_files(tmp_path):
    (tmp_path / "species.md").write_text("# Species", encoding="utf-8")
    (tmp_path / "techniques.md").write_text("# Techniques", encoding="utf-8")

    result = list_wiki_pages(tmp_path)

    assert_that(result, contains_string("species.md"), "Should include species.md")
    assert_that(result, contains_string("techniques.md"), "Should include techniques.md")


def test_should_exclude_non_markdown_files(tmp_path):
    (tmp_path / "page.md").write_text("# Page", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}", encoding="utf-8")

    result = list_wiki_pages(tmp_path)

    assert_that(result, not_(contains_string("data.json")), "Should not include non-.md files")


def test_should_include_nested_pages(tmp_path):
    nested = tmp_path / "species" / "ficus"
    nested.mkdir(parents=True)
    (nested / "index.md").write_text("# Ficus", encoding="utf-8")

    result = list_wiki_pages(tmp_path)

    assert_that(result, contains_string("index.md"), "Should include nested pages")


def test_should_return_empty_string_when_wiki_root_missing(tmp_path):
    result = list_wiki_pages(tmp_path / "nonexistent")

    assert_that(result, equal_to(""), "Should return empty string for missing wiki root")


from hamcrest import equal_to
