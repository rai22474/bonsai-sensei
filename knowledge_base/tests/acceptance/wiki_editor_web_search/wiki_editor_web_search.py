from hamcrest import assert_that, contains_string, not_none, greater_than

from pytest_bdd import given, parsers, scenario, then, when

from http_client import post, delete
from mcp_client import read_wiki_page, write_wiki_page

_EDITOR_CHAT_ID = "bdd-wiki-editor-web-search-test"


@scenario("../features/wiki_editor_web_search.feature", "Editor searches web and writes result to wiki page")
def test_editor_searches_web_and_writes_page():
    return None


@scenario("../features/wiki_editor_web_search.feature", "Editor combines web search with existing wiki content")
def test_editor_combines_web_and_existing():
    return None


@given(parsers.parse('no wiki page exists at "{page_path}"'))
def ensure_page_absent(context, page_path):
    try:
        delete(f"/api/wiki?path={page_path}")
    except Exception:
        pass
    context["wiki_paths_created"].append(page_path)


@given(parsers.parse('a wiki page "{page_path}" exists with content "{content}"'))
def create_wiki_page(context, page_path, content):
    write_wiki_page(page_path, content.replace("\\n", "\n"))
    context["wiki_paths_created"].append(page_path)
    page = read_wiki_page(page_path)
    context["content_before"] = page.get("content", "") if page else ""


@when(parsers.parse('the admin sends "{text}"'))
def admin_sends_message(context, text):
    post("/api/wiki/transcripts/wiki-editor/run/sync", {
        "chat_id": _EDITOR_CHAT_ID,
        "text": text,
    })


@then(parsers.parse('"{page_path}" exists in the wiki'))
def assert_page_exists(context, page_path):
    page = read_wiki_page(page_path)
    assert_that(page, not_none(), f"Page {page_path} should exist after web search")


@then(parsers.parse('"{page_path}" contains relevant content about "{topic}"'))
def assert_page_contains_topic(context, page_path, topic):
    page = read_wiki_page(page_path)
    assert_that(page.get("content", ""), contains_string(topic),
        f"Page {page_path} should contain content about {topic}")


@then(parsers.parse('"{page_path}" has more content than before'))
def assert_page_grew(context, page_path):
    page = read_wiki_page(page_path)
    content_after = page.get("content", "") if page else ""
    assert len(content_after) > len(context["content_before"]), \
        f"Page {page_path} should have more content after web search enrichment"
