import pytest
from hamcrest import assert_that, equal_to, none, has_length

from bonsai_sensei.knowledge_base.wiki_index.entry import IndexEntry
from bonsai_sensei.knowledge_base.wiki_index.store import save_entry, load_entry, load_all_entries


def should_save_and_load_entry(wiki_root):
    entry = IndexEntry(
        page_path="species/ficus.md",
        abstract="Ficus retusa is a tropical species.",
        links=["techniques/wiring.md"],
        embedding=[0.1, 0.2, 0.3],
    )

    save_entry(wiki_root, entry)
    loaded = load_entry(wiki_root, "species/ficus.md")

    assert_that(loaded.abstract, equal_to("Ficus retusa is a tropical species."), "Loaded abstract should match saved abstract")


def should_return_none_for_missing_entry(wiki_root):
    result = load_entry(wiki_root, "nonexistent/page.md")

    assert_that(result, none(), "Should return None when entry file does not exist")


def should_load_all_entries(wiki_root):
    entry_one = IndexEntry(page_path="page_one.md", abstract="First page", links=[], embedding=[0.1])
    entry_two = IndexEntry(page_path="page_two.md", abstract="Second page", links=[], embedding=[0.2])
    save_entry(wiki_root, entry_one)
    save_entry(wiki_root, entry_two)

    all_entries = load_all_entries(wiki_root)

    assert_that(all_entries, has_length(2), "Should load exactly 2 entries from wiki-index")


@pytest.fixture
def wiki_root(tmp_path):
    return tmp_path
