import re

from hamcrest import assert_that, contains_string, not_none
from pytest_bdd import scenario, when, then, parsers

from http_client import post
from mcp_client import read_wiki_page


@scenario("../features/episodic_memory.feature", "Dreamer incorporates bonsai observation into wiki")
def test_dreamer_incorporates_bonsai_observation():
    return None


@when("the wiki dreamer runs synchronously")
def run_dreamer_sync(context):
    post("/api/wiki/transcripts/wiki-dreamer/run/sync")


@then(parsers.parse('the wiki page for "{bonsai_name}" exists and contains information about the observation'))
def assert_wiki_page_updated(context, bonsai_name):
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    wiki_path = f"bonsai/{slug}/index.md"
    context["wiki_paths_created"].append(wiki_path)

    page = read_wiki_page(wiki_path)
    assert_that(page, not_none(), f"Wiki page {wiki_path} should exist after dreamer run")
    content = page.get("content", "")
    assert_that(content, contains_string("amarill"), "Wiki page should mention the reported symptom")
