from unittest.mock import MagicMock, call

import pytest
from falkordb.node import Node
from hamcrest import assert_that, equal_to, none, is_

from knowledge_base.wiki_index.entry import IndexEntry
from knowledge_base.wiki_index.store import create_save_entry, create_load_entry, create_load_all_entries


def should_save_entry_merges_node_and_links(graph):
    save_entry = create_save_entry(graph)
    entry = IndexEntry(
        page_path="species/ficus.md",
        abstract="Ficus retusa is a tropical species.",
        links=["techniques/wiring.md"],
        embedding=[0.1, 0.2, 0.3],
    )

    save_entry(entry)

    assert_that(graph.query.call_count, equal_to(2), "Should call query once for node merge and once for each link")


def should_load_entry_returns_entry_when_found(graph):
    node = Node(properties={
        'page_path': 'species/ficus.md',
        'abstract': 'Ficus retusa is a tropical species.',
        'embedding': [0.1, 0.2, 0.3],
    })
    links_result = MagicMock()
    links_result.result_set = []
    graph.query.side_effect = [
        MagicMock(result_set=[[node]]),
        links_result,
    ]
    load_entry = create_load_entry(graph)

    loaded = load_entry("species/ficus.md")

    assert_that(loaded.abstract, equal_to("Ficus retusa is a tropical species."), "Loaded abstract should match saved abstract")


def should_load_entry_returns_none_when_not_found(graph):
    graph.query.return_value = MagicMock(result_set=[])
    load_entry = create_load_entry(graph)

    result = load_entry("nonexistent/page.md")

    assert_that(result, none(), "Should return None when node not found in graph")


def should_load_all_entries_returns_entries(graph):
    node_one = Node(properties={'page_path': 'page_one.md', 'abstract': 'First page', 'embedding': [0.1]})
    node_two = Node(properties={'page_path': 'page_two.md', 'abstract': 'Second page', 'embedding': [0.2]})
    links_result = MagicMock(result_set=[])
    graph.query.side_effect = [
        MagicMock(result_set=[[node_one], [node_two]]),
        links_result,
        links_result,
    ]
    load_all_entries = create_load_all_entries(graph)

    entries = load_all_entries()

    assert_that(len(entries), equal_to(2), "Should return 2 entries from graph")


@pytest.fixture
def graph():
    mock = MagicMock()
    mock.query.return_value = MagicMock(result_set=[])
    return mock
