from hamcrest import assert_that, contains_string, not_

from knowledge_base.wiki_editor.tools.search_pages import search_wiki_pages


def test_should_find_matching_lines(tmp_path):
    (tmp_path / "fertilizers.md").write_text("Uso de Biorren en bonsái\nOtro contenido", encoding="utf-8")

    result = search_wiki_pages("Biorren", tmp_path)

    assert_that(result, contains_string("fertilizers.md"), "Should return path of matching file")
    assert_that(result, contains_string("Biorren"), "Should return the matching line")


def test_should_not_include_non_matching_files(tmp_path):
    (tmp_path / "match.md").write_text("Contiene Biorren", encoding="utf-8")
    (tmp_path / "no-match.md").write_text("Sin coincidencias", encoding="utf-8")

    result = search_wiki_pages("Biorren", tmp_path)

    assert_that(result, not_(contains_string("no-match.md")), "Should exclude files without matches")


def test_should_search_case_insensitively(tmp_path):
    (tmp_path / "page.md").write_text("El producto BIORREN es efectivo", encoding="utf-8")

    result = search_wiki_pages("biorren", tmp_path)

    assert_that(result, contains_string("page.md"), "Should find match regardless of case")


def test_should_support_regex_alternation(tmp_path):
    (tmp_path / "page.md").write_text("Ficus retusa\nOlea europea\nAcer palmatum", encoding="utf-8")

    result = search_wiki_pages(r"Ficus|Olea", tmp_path)

    assert_that(result, contains_string("Ficus retusa"), "Should match first alternative")
    assert_that(result, contains_string("Olea europea"), "Should match second alternative")
    assert_that(result, not_(contains_string("Acer")), "Should not match non-alternates")


def test_should_return_no_results_message_when_no_match(tmp_path):
    (tmp_path / "page.md").write_text("Contenido sin coincidencias", encoding="utf-8")

    result = search_wiki_pages("inexistente", tmp_path)

    assert_that(result, contains_string("No results"), "Should report no results")


def test_should_return_error_for_invalid_regex(tmp_path):
    (tmp_path / "page.md").write_text("content", encoding="utf-8")

    result = search_wiki_pages("[invalid", tmp_path)

    assert_that(result, contains_string("Invalid regex"), "Should report invalid regex error")


def test_should_include_line_numbers(tmp_path):
    (tmp_path / "page.md").write_text("line one\nBiorren here\nline three", encoding="utf-8")

    result = search_wiki_pages("Biorren", tmp_path)

    assert_that(result, contains_string(":2:"), "Should include line number in output")
