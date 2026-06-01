import re

from pytest_bdd import scenario, when, then, parsers

from http_client import advise
from manage_bonsai.wiki_api import get_wiki_page


def _wiki_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@scenario(
    "../features/fertilizer_recommendation.feature",
    "Ask for fertilizer recommendation saves recommendation to wiki",
)
def test_fertilizer_recommendation_saves_to_wiki():
    return None


@when(parsers.parse('I ask for fertilizer recommendation for "{bonsai_name}"'))
def ask_for_fertilizer_recommendation(context, bonsai_name):
    response = advise(
        text=f"¿Qué fertilizante me recomiendas para mi bonsái {bonsai_name}?",
        user_id=context["user_id"],
    )
    context["advice_response"] = response.get("text", "")
    context["asked_bonsai_name"] = bonsai_name


@then("the response should contain a fertilizer recommendation")
def assert_response_contains_recommendation(context):
    response_text = context.get("advice_response", "")
    assert len(response_text) > 50, (
        f"Expected a substantive fertilizer recommendation (>50 chars), got: '{response_text}'"
    )


@then(parsers.parse('the fertilization plan wiki page for "{bonsai_name}" should exist'))
def assert_fertilization_plan_wiki_page_exists(context, bonsai_name):
    wiki_path = f"bonsai/{_wiki_slug(bonsai_name)}/fertilization-plan.md"
    page = get_wiki_page(wiki_path)
    assert page is not None, (
        f"Expected fertilization plan wiki page at '{wiki_path}' to exist after recommendation, but it was not found"
    )
