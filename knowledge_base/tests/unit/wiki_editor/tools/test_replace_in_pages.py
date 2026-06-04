from hamcrest import assert_that, contains_string, not_

from knowledge_base.wiki_editor.tools.replace_in_pages import replace_in_pages


def test_should_replace_pattern_in_matching_page(tmp_path):
    (tmp_path / "page.md").write_text("Usa Biorren para fertilizar.", encoding="utf-8")

    replace_in_pages("Biorren", "Biorend", tmp_path)

    assert_that((tmp_path / "page.md").read_text(encoding="utf-8"),
        contains_string("Biorend"), "Should replace pattern with replacement")


def test_should_not_leave_old_pattern_after_replace(tmp_path):
    (tmp_path / "page.md").write_text("Usa Biorren para fertilizar.", encoding="utf-8")

    replace_in_pages("Biorren", "Biorend", tmp_path)

    assert_that((tmp_path / "page.md").read_text(encoding="utf-8"),
        not_(contains_string("Biorren")), "Should remove all occurrences of old pattern")


def test_should_replace_case_insensitively(tmp_path):
    (tmp_path / "page.md").write_text("El BIORREN es efectivo.", encoding="utf-8")

    replace_in_pages("biorren", "Biorend", tmp_path)

    assert_that((tmp_path / "page.md").read_text(encoding="utf-8"),
        contains_string("Biorend"), "Should replace case-insensitively")


def test_should_process_at_most_max_pages(tmp_path):
    for i in range(6):
        (tmp_path / f"page-{i}.md").write_text("Biorren aquí.", encoding="utf-8")

    replace_in_pages("Biorren", "Biorend", tmp_path, max_pages=3)

    fixed = sum(1 for i in range(6) if "Biorend" in (tmp_path / f"page-{i}.md").read_text())
    assert fixed == 3, f"Should fix exactly 3 pages, fixed {fixed}"


def test_should_report_remaining_pages_when_batch_incomplete(tmp_path):
    for i in range(6):
        (tmp_path / f"page-{i}.md").write_text("Biorren aquí.", encoding="utf-8")

    result = replace_in_pages("Biorren", "Biorend", tmp_path, max_pages=3)

    assert_that(result, contains_string("still have matches"), "Should report remaining pages")


def test_should_report_completion_when_all_fixed(tmp_path):
    (tmp_path / "page.md").write_text("Biorren.", encoding="utf-8")

    result = replace_in_pages("Biorren", "Biorend", tmp_path, max_pages=5)

    assert_that(result, contains_string("No more"), "Should report all done when no remaining")


def test_should_report_no_matches_when_pattern_absent(tmp_path):
    (tmp_path / "page.md").write_text("Sin coincidencias.", encoding="utf-8")

    result = replace_in_pages("Biorren", "Biorend", tmp_path)

    assert_that(result, contains_string("No pages"), "Should report no pages with matches")


def test_should_return_error_for_invalid_regex(tmp_path):
    (tmp_path / "page.md").write_text("content", encoding="utf-8")

    result = replace_in_pages("[invalid", "replacement", tmp_path)

    assert_that(result, contains_string("Invalid regex"), "Should report invalid regex error")


def test_should_replace_all_occurrences_within_a_page(tmp_path):
    (tmp_path / "page.md").write_text("Biorren y más Biorren.", encoding="utf-8")

    replace_in_pages("Biorren", "Biorend", tmp_path)

    content = (tmp_path / "page.md").read_text(encoding="utf-8")
    assert content.count("Biorend") == 2, "Should replace all occurrences within a page"
