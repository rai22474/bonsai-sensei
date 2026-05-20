import re

from hamcrest import assert_that, contains_string, not_none
from pytest_bdd import scenario, when, then, parsers

from http_client import advise, get, post


@scenario("../features/episodic_memory.feature", "Keeper incorporates bonsai observation from conversation into wiki")
def test_keeper_incorporates_bonsai_observation():
    return None


@when(parsers.parse('I report "{observation}"'))
def report_observation(context, observation):
    advise(text=observation, user_id=context["user_id"])


@when("the wiki keeper runs synchronously")
def run_keeper_sync(context):
    post("/api/wiki/transcripts/wiki-keeper/run/sync")


@then(parsers.parse('the wiki page for "{bonsai_name}" exists and contains information about the observation'))
def assert_wiki_page_updated(context, bonsai_name):
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    wiki_path = f"bonsai/{slug}/index.md"
    response = get(f"/api/wiki?path={wiki_path}")

    assert_that(response, not_none(), "wiki page should exist after keeper run")
    content = response.get("content", "")
    assert_that(
        content,
        contains_string("amarill"),
        "wiki page should mention the reported symptom (hojas amarillas)",
    )
