from hamcrest import assert_that, not_, equal_to, has_item, empty
from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario("../features/analyze_stored_photo.feature", "Visual description is returned for the latest stored photo")
def test_visual_description_for_latest_photo():
    return None


@scenario("../features/analyze_stored_photo.feature", "Photo from approximate date is identified and described")
def test_photo_from_approximate_date():
    return None


@scenario("../features/analyze_stored_photo.feature", "No photos available returns an explanation")
def test_no_photos_available():
    return None


@when(parsers.parse('I ask to analyse the latest photo of bonsai "{bonsai_name}"'))
def ask_to_analyse_latest_photo(context, bonsai_name):
    response = advise(
        text=f"Analiza la última foto de '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@when(parsers.parse('I ask to analyse the photo of bonsai "{bonsai_name}" from "{date_text}"'))
def ask_to_analyse_photo_from_date(context, bonsai_name, date_text):
    response = advise(
        text=f"Analiza la foto de '{bonsai_name}' de {date_text}.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then("I receive a visual description of the photo")
def assert_visual_description_received(context):
    response_text = context.get("advice_response", {}).get("text", "")
    assert_that(response_text, not_(equal_to("")), "Expected a non-empty visual description")


@then(parsers.parse('I receive an analysis of the photo taken on "{taken_on}"'))
def assert_analysis_of_correct_photo(context, taken_on):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a non-empty analysis")
    assert_that(response.get("photos_taken_on", []), has_item(taken_on), f"Expected photos_taken_on to include {taken_on}")


@then(parsers.parse('I am informed that no photos are available for "{bonsai_name}"'))
def assert_no_photos_available(context, bonsai_name):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a non-empty response explaining no photos")
    assert_that(response.get("photos_taken_on", []), empty(), "Expected no photo to have been analyzed")
