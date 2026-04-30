from hamcrest import assert_that, not_, equal_to
from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario("../features/analyze_stored_photo.feature", "Visual description is returned for the latest stored photo")
def test_visual_description_for_latest_photo():
    return None


@when(parsers.parse('I ask to analyse the latest photo of bonsai "{bonsai_name}"'))
def ask_to_analyse_latest_photo(context, bonsai_name):
    response = advise(
        text=f"Analiza la última foto de '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then("I receive a visual description of the photo")
def assert_visual_description_received(context):
    response_text = context.get("advice_response", {}).get("text", "")
    assert_that(response_text, not_(equal_to("")), "Expected a non-empty visual description")
