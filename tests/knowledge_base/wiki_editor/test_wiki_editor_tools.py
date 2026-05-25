import pytest
from hamcrest import assert_that, contains_string, equal_to, not_

from bonsai_sensei.knowledge_base.wiki_editor.agent import list_wiki_pages, read_wiki_page, search_wiki_pages, write_wiki_page


def should_read_existing_page(tmp_path):
    page_file = tmp_path / "species" / "ficus.md"
    page_file.parent.mkdir(parents=True)
    page_file.write_text("# Ficus Retusa", encoding="utf-8")

    result = read_wiki_page("species/ficus.md", tmp_path)

    assert_that(result, contains_string("# Ficus Retusa"), "Should return the content of the existing page")


def should_write_new_page(tmp_path):
    write_wiki_page("techniques/wiring.md", "# Wiring technique", tmp_path)

    written_file = tmp_path / "techniques" / "wiring.md"
    assert_that(written_file.read_text(encoding="utf-8"), equal_to("# Wiring technique"), "Should create file with correct content")


def should_list_pages(tmp_path):
    (tmp_path / "species.md").write_text("# Species", encoding="utf-8")
    (tmp_path / "techniques.md").write_text("# Techniques", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}", encoding="utf-8")

    result = list_wiki_pages(tmp_path)

    assert_that(result, contains_string("species.md"), "Should include .md files in the list")
    assert_that(result, contains_string("techniques.md"), "Should include all .md files")
    assert_that(result, not_(contains_string("data.json")), "Should not include non-.md files")


def should_find_matching_lines(tmp_path):
    (tmp_path / "fertilizers.md").write_text("Uso de Biorren en bonsái\nOtro contenido", encoding="utf-8")
    (tmp_path / "species.md").write_text("Sin coincidencias aquí", encoding="utf-8")

    result = search_wiki_pages("Biorren", tmp_path)

    assert_that(result, contains_string("fertilizers.md"), "Should return path of matching file")
    assert_that(result, contains_string("Biorren"), "Should return the matching line content")
    assert_that(result, not_(contains_string("species.md")), "Should not include files without matches")


def should_search_case_insensitively(tmp_path):
    (tmp_path / "page.md").write_text("El producto BIORREN es efectivo", encoding="utf-8")

    result = search_wiki_pages("biorren", tmp_path)

    assert_that(result, contains_string("page.md"), "Should find match regardless of case")


def should_support_regex_patterns(tmp_path):
    (tmp_path / "page.md").write_text("Ficus retusa\nOlea europea\nAcer palmatum", encoding="utf-8")

    result = search_wiki_pages(r"Ficus|Olea", tmp_path)

    assert_that(result, contains_string("Ficus retusa"), "Should match first alternative")
    assert_that(result, contains_string("Olea europea"), "Should match second alternative")
    assert_that(result, not_(contains_string("Acer")), "Should not match non-alternates")


def should_return_error_for_invalid_regex(tmp_path):
    (tmp_path / "page.md").write_text("content", encoding="utf-8")

    result = search_wiki_pages("[invalid", tmp_path)

    assert_that(result, contains_string("Invalid regex"), "Should report invalid regex error")
