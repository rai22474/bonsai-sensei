from hamcrest import assert_that, contains_string, less_than_or_equal_to

from pytest_bdd import given, parsers, scenario, then, when

from http_client import post, delete, get
from mcp_client import read_wiki_page, write_wiki_page


@scenario("../features/wiki_dreamer_wikilinks.feature", "Dreamer adds a wikilink when a page mentions an entity that has its own page")
def test_dreamer_adds_wikilink():
    return None


@scenario("../features/wiki_dreamer_wikilinks.feature", "Dreamer processes at most 5 pages per run for wikilinks")
def test_dreamer_batch_limit():
    return None


@scenario("../features/wiki_dreamer_wikilinks.feature", "Dreamer skips pages already processed for wikilinks unless they changed")
def test_dreamer_skips_processed():
    return None


@given(parsers.parse('a wiki page "{page_path}" exists with content "{content}"'))
def create_wiki_page(context, page_path, content):
    write_wiki_page(page_path, content)
    context["wiki_paths_created"].append(page_path)


@given(parsers.parse('the wikilink tracker is reset for "{page_path}"'))
def reset_wikilink_for_page(context, page_path):
    delete(f"/api/wiki/transcripts/wiki-dreamer/wikilinks/pages?path={page_path}")


@given("7 knowledge pages exist without wikilinks processed")
def create_seven_pages(context):
    post("/api/wiki/transcripts/wiki-dreamer/wikilinks/reset")
    for i in range(7):
        path = f"techniques/test-wl-batch-{i}.md"
        write_wiki_page(path, f"# Técnica {i}\n\nContenido de prueba.")
        context["wiki_paths_created"].append(path)


@given(parsers.parse('the wikilink tracker marks "{page_path}" as processed'))
def mark_page_as_processed(context, page_path):
    post(f"/api/wiki/transcripts/wiki-dreamer/wikilinks/pages?path={page_path}")
    context["marked_as_processed"] = page_path


@when("the wiki dreamer runs synchronously")
def run_dreamer(context):
    context["wikilink_tracker_before"] = _get_wikilink_tracker()
    post("/api/wiki/transcripts/wiki-dreamer/run/sync")
    context["wikilink_tracker_after"] = _get_wikilink_tracker()
    before_keys = set(context["wikilink_tracker_before"].keys())
    after_keys = set(context["wikilink_tracker_after"].keys())
    context["wikilinks_newly_processed"] = after_keys - before_keys


@then(parsers.parse('the wiki page "{page_path}" contains "{text}"'))
def assert_page_contains(context, page_path, text):
    page = read_wiki_page(page_path)
    assert_that(page.get("content", ""), contains_string(text),
        f"Page {page_path} should contain '{text}' after dreamer run")


@then("at most 5 pages are marked as wikilink-processed in this run")
def assert_batch_limit(context):
    newly_processed = len(context.get("wikilinks_newly_processed", set()))
    assert_that(newly_processed, less_than_or_equal_to(5),
        f"Dreamer processed {newly_processed} pages but should process at most 5 per run")


@then(parsers.parse('"{page_path}" is not included in the wikilink batch'))
def assert_page_not_in_batch(context, page_path):
    newly_processed = context.get("wikilinks_newly_processed", set())
    assert page_path not in newly_processed, \
        f"Already-processed page {page_path} should not be re-processed. Newly processed: {newly_processed}"


def _get_wikilink_tracker() -> dict:
    try:
        result = get("/api/wiki/transcripts/wiki-dreamer/wikilinks/tracker")
        return result or {}
    except Exception:
        return {}
