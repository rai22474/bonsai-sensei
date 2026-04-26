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
