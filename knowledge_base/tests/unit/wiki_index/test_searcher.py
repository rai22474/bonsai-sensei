from unittest.mock import MagicMock

import pytest
from hamcrest import assert_that, equal_to, close_to

from knowledge_base.wiki_index.searcher import create_search_by_embedding


def should_return_top_k_results_sorted_by_similarity(graph):
    graph.query.return_value = MagicMock(result_set=[
        ['match.md', 'Highly relevant', 0.0],
        ['other.md', 'Less relevant', 0.3],
    ])
    search_by_embedding = create_search_by_embedding(graph)

    results = search_by_embedding([1.0, 0.0, 0.0], top_k=3)

    assert_that(results[0][0], equal_to("match.md"), "First result should be the most similar entry")


def should_convert_distance_to_similarity(graph):
    graph.query.return_value = MagicMock(result_set=[
        ['page.md', 'Content', 0.4],
    ])
    search_by_embedding = create_search_by_embedding(graph)

    results = search_by_embedding([1.0, 0.0], top_k=1)

    assert_that(results[0][2], close_to(0.6, 0.000001), "Score should be 1 - distance")


def should_return_empty_when_no_results(graph):
    graph.query.return_value = MagicMock(result_set=[])
    search_by_embedding = create_search_by_embedding(graph)

    results = search_by_embedding([0.5, 0.5, 0.5], top_k=5)

    assert_that(results, equal_to([]), "Should return empty list when graph returns no results")


def should_include_user_id_filter_in_query_when_provided(graph):
    graph.query.return_value = MagicMock(result_set=[])
    search_by_embedding = create_search_by_embedding(graph)

    search_by_embedding([0.1, 0.2], top_k=3, user_id="user123")

    call_args = graph.query.call_args
    assert_that("$user_id" in call_args[0][0], equal_to(True), "Query should contain user_id filter when user_id is provided")


def should_restrict_to_global_pages_when_user_id_is_none(graph):
    graph.query.return_value = MagicMock(result_set=[])
    search_by_embedding = create_search_by_embedding(graph)

    search_by_embedding([0.1, 0.2], top_k=3, user_id=None)

    call_args = graph.query.call_args
    assert_that("user_id IS NULL" in call_args[0][0], equal_to(True), "Query should restrict to global pages when user_id is None")


@pytest.fixture
def graph():
    mock = MagicMock()
    mock.query.return_value = MagicMock(result_set=[])
    return mock
