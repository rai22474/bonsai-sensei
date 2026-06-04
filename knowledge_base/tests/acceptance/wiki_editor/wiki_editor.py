from hamcrest import assert_that, contains_string, not_

from pytest_bdd import given, parsers, scenario, then, when

from http_client import post
from mcp_client import read_wiki_page, write_wiki_page

_EDITOR_CHAT_ID = "bdd-wiki-editor-test"


@scenario("../features/wiki_editor.feature", "Editor fixes a misspelling across multiple pages in batches")
def test_editor_fixes_misspelling():
    return None


@scenario("../features/wiki_editor.feature", "Editor updates a specific page with new content")
def test_editor_updates_page():
    return None


@scenario("../features/wiki_editor.feature", "Editor reports pages fixed and pending when batch limit is reached")
def test_editor_batch_report():
    return None


@given(parsers.parse('a wiki page "{page_path}" exists with content "{content}"'))
def create_wiki_page(context, page_path, content):
    write_wiki_page(page_path, content.replace("\\n", "\n"))
    context["wiki_paths_created"].append(page_path)


@given(parsers.parse('6 wiki pages in "{directory}" all containing the word "Biorren"'))
def create_six_pages_with_biorren(context, directory):
    for i in range(6):
        path = f"{directory}/page-{i}.md"
        write_wiki_page(path, f"# Página {i}\n\nUsa Biorren para fertilizar.")
        context["wiki_paths_created"].append(path)


@when(parsers.parse('the admin sends "{text}"'))
def admin_sends_message(context, text):
    result = post("/api/wiki/transcripts/wiki-editor/run/sync", {
        "chat_id": _EDITOR_CHAT_ID,
        "text": text,
    })
    context["editor_response"] = result.get("response", "")


@then(parsers.parse('"{page_path}" contains "{text}"'))
def assert_page_contains(context, page_path, text):
    page = read_wiki_page(page_path)
    assert_that(page.get("content", ""), contains_string(text),
        f"Page {page_path} should contain '{text}'")


@then(parsers.parse('"{page_path}" does not contain "{text}"'))
def assert_page_not_contains(context, page_path, text):
    page = read_wiki_page(page_path)
    assert_that(page.get("content", ""), not_(contains_string(text)),
        f"Page {page_path} should not contain '{text}'")


@then("the editor response mentions pages were fixed")
def assert_response_mentions_fixed(context):
    response = context["editor_response"].lower()
    assert any(word in response for word in ["fixed", "correg", "reemplaz", "actualiz", "página"]), \
        f"Editor response should mention pages fixed. Got: {context['editor_response']}"


@then("the editor response mentions remaining pages or completion")
def assert_response_mentions_remaining_or_done(context):
    response = context["editor_response"].lower()
    has_remaining = any(w in response for w in ["quedan", "remain", "pending", "pendiente"])
    has_done = any(w in response for w in ["completado", "done", "no more", "ninguna más", "todas"])
    assert has_remaining or has_done, \
        f"Editor response should mention remaining or completion. Got: {context['editor_response']}"
