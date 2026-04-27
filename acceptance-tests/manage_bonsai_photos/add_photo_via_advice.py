from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, upload_photo, advise
from manage_bonsai_photos.conftest import (
    create_species_record,
    create_bonsai_record,
    create_bonsai_photo_via_api,
    find_bonsai_by_name_api,
    get_species_record_id,
    list_bonsai_photos,
    MINIMAL_PNG,
)


@scenario("../features/manage_bonsai_photos.feature", "Add a photo to a bonsai")
def test_add_photo_to_bonsai():
    return None


@scenario("../features/manage_bonsai_photos.feature", "Add multiple photos to a bonsai accumulates them")
def test_add_multiple_photos_accumulates():
    return None


@scenario("../features/manage_bonsai_photos.feature", "Add a photo when the bonsai does not exist returns an error")
def test_add_photo_bonsai_not_found():
    return None


@scenario("../features/manage_bonsai_photos.feature", "Retrieve the latest photo of a bonsai")
def test_retrieve_latest_photo():
    return None


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    create_species_record(context, name, scientific_name)


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = get_species_record_id(context, species_name)
    create_bonsai_record(context, bonsai_name, species_id)


@when("I send a photo")
def send_photo(context):
    response = upload_photo(MINIMAL_PNG, user_id=context["user_id"])
    context["photo_path"] = response.get("photo_path")


@when(parsers.parse('I confirm the photo belongs to bonsai "{bonsai_name}"'))
def confirm_photo_bonsai(context, bonsai_name):
    photo_path = context.get("photo_path", "")
    response = advise(
        text=f"Registra la foto '{photo_path}' para el bonsái '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response
    pending_confirmations = response.get("pending_confirmations", [])
    for confirmation in pending_confirmations:
        accept_confirmation(context["user_id"], confirmation["id"])


@given(parsers.parse('bonsai "{bonsai_name}" already has 1 photo'))
def ensure_bonsai_has_one_photo_already(context, bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    create_bonsai_photo_via_api(bonsai["id"], MINIMAL_PNG)


@then(parsers.parse('bonsai "{bonsai_name}" should have 1 photo'))
def assert_bonsai_has_one_photo(context, bonsai_name):
    from hamcrest import assert_that, equal_to
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to exist"
    photos = list_bonsai_photos(bonsai["id"])
    assert_that(len(photos), equal_to(1), f"Expected bonsai '{bonsai_name}' to have 1 photo")


@then(parsers.parse('bonsai "{bonsai_name}" should have 2 photos'))
def assert_bonsai_has_two_photos(context, bonsai_name):
    from hamcrest import assert_that, equal_to
    bonsai = find_bonsai_by_name_api(bonsai_name)
    photos = list_bonsai_photos(bonsai["id"])
    assert_that(len(photos), equal_to(2), f"Expected bonsai '{bonsai_name}' to have 2 photos")


@given(parsers.parse('no bonsai named "{bonsai_name}" exists'))
def ensure_bonsai_does_not_exist(context, bonsai_name):
    from http_client import delete as delete_request
    bonsai = find_bonsai_by_name_api(bonsai_name)
    if bonsai:
        delete_request(f"/api/bonsai/{bonsai['id']}")


@then("I should receive an error indicating the bonsai does not exist")
def assert_bonsai_not_found_error(context):
    from hamcrest import assert_that, empty
    pending = context.get("advice_response", {}).get("pending_confirmations", [])
    assert_that(pending, empty(), "Expected no confirmation request when bonsai does not exist")


@given(parsers.parse('bonsai "{bonsai_name}" has a photo taken on "{taken_on}"'))
def ensure_bonsai_has_photo_on_date(context, bonsai_name, taken_on):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    create_bonsai_photo_via_api(bonsai["id"], MINIMAL_PNG, taken_on=taken_on)


@when(parsers.parse('I ask for the latest photo of bonsai "{bonsai_name}"'))
def ask_for_latest_photo(context, bonsai_name):
    response = advise(
        text=f"Muéstrame la última foto de '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@then(parsers.parse('I should receive the photo of bonsai "{bonsai_name}" taken on "{taken_on}"'))
def assert_photo_taken_on(context, bonsai_name, taken_on):
    from hamcrest import assert_that, has_item
    bonsai = find_bonsai_by_name_api(bonsai_name)
    photos = list_bonsai_photos(bonsai["id"])
    expected_photo = next((photo for photo in photos if photo["taken_on"] == taken_on), None)
    assert expected_photo is not None, f"No photo found with taken_on='{taken_on}' for bonsai '{bonsai_name}'"
    response_photos = context.get("advice_response", {}).get("photos", [])
    assert_that(response_photos, has_item(expected_photo["file_path"]), f"Expected response photos to include '{expected_photo['file_path']}'")
