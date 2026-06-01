from hamcrest import assert_that, not_, equal_to, empty
from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario("../features/design_critique_bonsai.feature", "Design feedback references visible structural elements of the tree")
def test_design_feedback_for_latest_photo():
    return None


@scenario("../features/design_critique_bonsai.feature", "No stored photos prompts for a photo before design advice is given")
def test_no_photos_prompts_for_design_advice():
    return None


@when(parsers.parse('I ask to analyse the design of the latest photo of bonsai "{bonsai_name}"'))
def ask_to_analyse_design(context, bonsai_name):
    response = advise(
        text=f"Analiza la última foto de '{bonsai_name}' enfocándote solo en el diseño.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then("I receive design feedback referencing visible structural elements of the tree")
def assert_design_feedback_received(context):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a non-empty design critique")
    assert_that(response.get("photos_taken_on", []), not_(empty()), "Expected a photo to have been analysed")


@then("I am asked to provide a photo before receiving design advice")
def assert_prompted_for_photo_design(context):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a response asking for a photo")
    assert_that(response.get("photos_taken_on", []), empty(), "Expected no photo to have been analysed")
