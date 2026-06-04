from hamcrest import assert_that, not_, empty

from pytest_bdd import given, parsers, scenario, then, when

from http_client import post
from mcp_client import write_wiki_page


@scenario("../features/wiki_search.feature", "Search returns a page whose content matches the query")
def test_search_finds_matching_page():
    return None


@scenario("../features/wiki_search.feature", "Search returns multiple results ordered by relevance")
def test_search_ordered_by_relevance():
    return None


@scenario("../features/wiki_search.feature", "Search returns results with a relevance score")
def test_search_no_match():
    return None


@given(parsers.parse('a wiki page "{page_path}" exists with content "{content}"'))
def create_wiki_page(context, page_path, content):
    write_wiki_page(page_path, content)
    context["wiki_paths_created"].append(page_path)


@given("the wiki index is rebuilt")
def rebuild_index_given(context):
    post("/api/wiki/index/rebuild")


@when("the wiki index is rebuilt")
def rebuild_index_when(context):
    post("/api/wiki/index/rebuild")


@when(parsers.parse('the wiki is searched for "{query}"'))
def search(context, query):
    result = post("/api/wiki/index/search", {"query": query, "top_k": 5})
    context["search_results"] = result.get("results", []) if isinstance(result, dict) else []


@then(parsers.parse('the search results contain a page with path "{page_path}"'))
def assert_result_contains_path(context, page_path):
    paths = [r.get("page_path", "") for r in context["search_results"]]
    assert any(page_path in path for path in paths), \
        f"Search results should contain {page_path}. Got: {paths}"


@then(parsers.parse('the first search result has path "{page_path}"'))
def assert_first_result_path(context, page_path):
    results = context["search_results"]
    assert_that(results, not_(empty()), "Search should return results")
    first_path = results[0].get("page_path", "")
    assert first_path == page_path, \
        f"First result should be {page_path}, got {first_path}"


@then("the first search result has a relevance score above 0.5")
def assert_score_above_threshold(context):
    results = context["search_results"]
    assert results, "Search should return at least one result"
    top_score = results[0].get("score", 0.0)
    assert top_score > 0.5, \
        f"Top score {top_score} should be above 0.5 for a relevant query"
