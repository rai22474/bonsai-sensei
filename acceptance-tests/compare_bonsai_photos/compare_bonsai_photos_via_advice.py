from hamcrest import assert_that, not_, equal_to, empty, has_length
from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario("../features/compare_bonsai_photos.feature", "Observable changes are described when comparing two photos from different dates")
def test_observable_changes_described():
    return None


@scenario("../features/compare_bonsai_photos.feature", "Only one photo available returns an explanation and offers to analyse it")
def test_only_one_photo_available():
    return None


@scenario("../features/compare_bonsai_photos.feature", "No photos available returns an explanation")
def test_no_photos_available():
    return None


@when(parsers.parse('I ask to compare the photos of "{bonsai_name}" from "{date_context}"'))
def ask_to_compare_photos_with_context(context, bonsai_name, date_context):
    response = advise(
        text=f"Compara las fotos de '{bonsai_name}' de {date_context}.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@when(parsers.parse('I ask to compare the photos of "{bonsai_name}"'))
def ask_to_compare_photos(context, bonsai_name):
    response = advise(
        text=f"Compara las fotos de '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then("I receive a description of observable changes between the two photos")
def assert_changes_described(context):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a non-empty comparison description")
    assert_that(response.get("photos_taken_on", []), has_length(2), "Expected both compared photos to be tracked")


@then("I am informed that only one photo is available")
def assert_only_one_photo_informed(context):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a response informing about the single photo")


@then("I am offered to analyse the single photo instead")
def assert_offered_to_analyse_single(context):
    response_text = context.get("advice_response", {}).get("text", "")
    assert_that(response_text, not_(equal_to("")), "Expected an offer to analyse the single photo")


@then(parsers.parse('I am informed that no photos are available for "{bonsai_name}"'))
def assert_no_photos_available(context, bonsai_name):
    response = context.get("advice_response", {})
    assert_that(response.get("text", ""), not_(equal_to("")), "Expected a response explaining no photos are available")
    assert_that(response.get("photos_taken_on", []), empty(), "Expected no photos to have been analysed")
