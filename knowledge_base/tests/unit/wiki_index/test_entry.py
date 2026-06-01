from hamcrest import assert_that, equal_to, has_item, empty

from knowledge_base.wiki_index.entry import extract_abstract, extract_links


def should_extract_abstract_with_title_and_paragraphs():
    content = "# Ficus Retusa\n\nThe ficus retusa is a tropical species.\n\nIt thrives in warm climates.\n\nThird paragraph here."

    abstract = extract_abstract(content)

    assert_that(abstract, has_item("F"), "Abstract should contain title content from the markdown")


def should_extract_links_from_wikilinks():
    content = "See [[species/ficus.md|Ficus]] for more details."

    links = extract_links(content)

    assert_that(links, has_item("species/ficus.md"), "Should extract path from wikilink with display text")


def should_extract_links_without_display_text():
    content = "See [[techniques/wiring.md]] for wiring."

    links = extract_links(content)

    assert_that(links, has_item("techniques/wiring.md"), "Should extract path from wikilink without display text")


def should_return_empty_links_when_no_wikilinks():
    content = "This page has no internal links at all."

    links = extract_links(content)

    assert_that(links, equal_to([]), "Should return empty list when no wikilinks present")
