from hamcrest import assert_that, equal_to, contains_string, not_

from bonsai_sensei.domain.services.garden.nursery.bonsai_index_page import (
    build_bonsai_wiki_path,
    build_bonsai_index_page,
)


def should_build_path_for_simple_name():
    result = build_bonsai_wiki_path("Olmo")

    assert_that(result, equal_to("bonsai/olmo/index.md"), "Simple name should produce lowercase slug path")


def should_slugify_name_with_spaces():
    result = build_bonsai_wiki_path("Olmo chino")

    assert_that(result, equal_to("bonsai/olmo-chino/index.md"), "Spaces should be replaced with hyphens")


def should_slugify_name_with_special_chars():
    result = build_bonsai_wiki_path("Árbol #1")

    assert_that(result, equal_to("bonsai/rbol-1/index.md"), "Non-alphanumeric characters should be stripped")


def should_include_bonsai_name_in_heading():
    result = build_bonsai_index_page("Olmo", "Olmo", None)

    assert_that(result, contains_string("# Olmo"), "Page should include bonsai name as heading")


def should_include_species_as_wiki_link_when_path_provided():
    result = build_bonsai_index_page("Olmo", "Olmo", "species/path")

    assert_that(result, contains_string("[[species/path|Olmo]]"), "Species should be a wiki link when path is provided")


def should_include_species_as_plain_text_when_no_path():
    result = build_bonsai_index_page("Olmo", "Olmo", None)

    assert_that(result, not_(contains_string("[[species/")), "Species should be plain text when no path is provided")


def should_include_plans_link_in_page():
    result = build_bonsai_index_page("Olmo", "Olmo", None)

    assert_that(result, contains_string("plans/index.md"), "Page should include a link to plans")


def should_include_reports_link_in_page():
    result = build_bonsai_index_page("Olmo", "Olmo", None)

    assert_that(result, contains_string("reports/index.md"), "Page should include a link to reports")
