from functools import partial

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.knowledge_base.wiki_index.entry import IndexEntry
from bonsai_sensei.knowledge_base.wiki_index.searcher import search_by_embedding
from bonsai_sensei.knowledge_base.wiki_index.store import load_all_entries, save_entry


def should_return_top_k_results_by_similarity(wiki_root):
    matching_entry = IndexEntry(page_path="match.md", abstract="Highly relevant", links=[], embedding=[1.0, 0.0, 0.0])
    other_entry_one = IndexEntry(page_path="other_one.md", abstract="Less relevant", links=[], embedding=[0.0, 1.0, 0.0])
    other_entry_two = IndexEntry(page_path="other_two.md", abstract="Least relevant", links=[], embedding=[0.0, 0.0, 1.0])
    save_entry(wiki_root, matching_entry)
    save_entry(wiki_root, other_entry_one)
    save_entry(wiki_root, other_entry_two)

    results = search_by_embedding([1.0, 0.0, 0.0], partial(load_all_entries, wiki_root), top_k=3)

    assert_that(results[0][0], equal_to("match.md"), "First result should be the most similar entry")


def should_return_empty_when_no_entries(wiki_root):
    results = search_by_embedding([0.5, 0.5, 0.5], partial(load_all_entries, wiki_root), top_k=5)

    assert_that(results, equal_to([]), "Should return empty list when wiki-index has no entries")


@pytest.fixture
def wiki_root(tmp_path):
    return tmp_path
