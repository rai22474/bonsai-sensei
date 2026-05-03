from hamcrest import assert_that, empty, not_
from pytest_bdd import scenario, when, then, parsers

from http_client import advise
from manage_bonsai_photos.conftest import find_bonsai_by_name_api, list_bonsai_photos


@scenario(
    "../features/manage_bonsai_photos.feature",
    "Listing registered photo dates does not display the images",
)
def test_listing_photo_dates_does_not_display_images():
    return None


@scenario(
    "../features/manage_bonsai_photos.feature",
    "Asking to show photos of a bonsai displays the images",
)
def test_asking_to_show_photos_displays_images():
    return None


@when(parsers.parse('I ask which photos bonsai "{bonsai_name}" has registered'))
def ask_which_photos_bonsai_has(context, bonsai_name):
    response = advise(
        text=f"¿Qué fotos tiene registradas el bonsái '{bonsai_name}'?",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@when(parsers.parse('I ask to show the photos of bonsai "{bonsai_name}"'))
def ask_to_show_photos(context, bonsai_name):
    response = advise(
        text=f"Muéstrame todas las fotos de '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then("I should receive the photo dates in the text without any images being sent")
def assert_no_images_returned(context):
    response_photos = context["advice_response"].get("photos", [])
    assert_that(response_photos, empty(), "Expected no photo images when only querying photo metadata")


@then("I should receive the images in the response")
def assert_images_returned(context):
    response_photos = context["advice_response"].get("photos", [])
    assert_that(response_photos, not_(empty()), "Expected photo images to be included in the response")
