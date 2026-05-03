from hamcrest import assert_that, not_, equal_to, empty
from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario("../features/diagnose_bonsai_health.feature", "Health analysis is returned for the latest stored photo")
def test_health_analysis_for_latest_photo():
    return None


@scenario("../features/diagnose_bonsai_health.feature", "No stored photos prompts for a photo before health advice is given")
def test_no_photos_prompts_for_photo():
    return None


@when(parsers.parse('I ask to analyse the health of the latest photo of bonsai "{bonsai_name}"'))
def ask_to_analyse_health(context, bonsai_name):
    response = advise(
        text=f"Analiza la última foto de '{bonsai_name}' enfocándote solo en la salud.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then("I receive a health analysis of the photo")
def assert_health_analysis_received(context):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a non-empty health analysis")
    assert_that(response.get("photos_taken_on", []), not_(empty()), "Expected a photo to have been analysed")


@then("I receive at least one actionable recommendation")
def assert_actionable_recommendation_received(context):
    response_text = context.get("advice_response", {}).get("text", "")
    assert_that(response_text, not_(equal_to("")), "Expected at least one actionable recommendation in the response")


@then("I am asked to provide a photo before receiving health advice")
def assert_prompted_for_photo(context):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a response asking for a photo")
    assert_that(response.get("photos_taken_on", []), empty(), "Expected no photo to have been analysed")
