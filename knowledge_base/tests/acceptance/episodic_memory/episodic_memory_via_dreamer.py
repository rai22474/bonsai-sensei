import re

from hamcrest import assert_that, contains_string, not_none, not_
from pytest_bdd import scenario, when, then, parsers

from http_client import get, post
from mcp_client import read_wiki_page


@scenario("../features/episodic_memory.feature", "Dreamer routes bonsai observation to user bonsai zone")
def test_dreamer_routes_bonsai_observation():
    return None


@scenario("../features/episodic_memory.feature", "Dreamer routes technique observation to user techniques-notes")
def test_dreamer_routes_technique_observation():
    return None


@scenario("../features/episodic_memory.feature", "Dreamer routes global observation to global wiki")
def test_dreamer_routes_global_observation():
    return None


@when("the wiki dreamer runs synchronously")
def run_dreamer_sync(context):
    post("/api/wiki/transcripts/wiki-dreamer/run/sync")


@then(parsers.parse('the wiki page "{wiki_path}" exists and contains "{text}"'))
def assert_wiki_page_contains(context, wiki_path, text):
    context["wiki_paths_created"].append(wiki_path)
    page = read_wiki_page(wiki_path)
    assert_that(page, not_none(), f"Wiki page {wiki_path} should exist after dreamer run")
    content = page.get("content", "")
    assert_that(content, contains_string(text), f"Wiki page should contain '{text}'")


@then(parsers.parse('a wiki page exists under "{directory}" containing "{text}"'))
def assert_user_directory_has_page_containing(context, directory, text):
    result = get(f"/api/wiki/files?directory={directory}")
    files = result if isinstance(result, list) else []
    assert files, f"No wiki pages found under {directory}"
    context["wiki_paths_created"].extend(files)
    found = False
    for file_path in files:
        page = read_wiki_page(file_path)
        if page and text.lower() in page.get("content", "").lower():
            found = True
            break
    assert found, f"No page under {directory} contains '{text}'"


@then(parsers.parse('a wiki page exists in the global wiki containing "{text}"'))
def assert_global_wiki_has_page_containing(context, text):
    for directory in ("diseases", "pests", "techniques", "species"):
        result = get(f"/api/wiki/files?directory={directory}")
        files = result if isinstance(result, list) else []
        for file_path in files:
            page = read_wiki_page(file_path)
            if page and text.lower() in page.get("content", "").lower():
                return
    assert False, f"No global wiki page found containing '{text}'"
