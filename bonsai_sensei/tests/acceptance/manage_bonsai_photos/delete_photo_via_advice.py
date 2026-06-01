from pytest_bdd import scenario, when, then, parsers
from hamcrest import assert_that, equal_to

from http_client import accept_confirmation, reject_confirmation, advise, choose_selection
from manage_bonsai_photos.conftest import find_bonsai_by_name_api, list_bonsai_photos


@scenario("../features/manage_bonsai_photos.feature", "Delete a photo from a bonsai")
def test_delete_photo_from_bonsai():
    return None


@scenario("../features/manage_bonsai_photos.feature", "Cancel a photo deletion preserves the photo")
def test_cancel_photo_deletion():
    return None


@scenario("../features/manage_bonsai_photos.feature", "Delete a photo when the bonsai does not exist returns an error")
def test_delete_photo_bonsai_not_found():
    return None


@when(parsers.parse('I ask to delete a photo of bonsai "{bonsai_name}"'))
def ask_to_delete_photo(context, bonsai_name):
    response = advise(
        text=f"Quiero eliminar una foto del bonsái '{bonsai_name}'.",
        user_id=context["user_id"],
    )
    context["advice_response"] = response


@when(parsers.parse('I select the photo taken on "{taken_on}"'))
def select_photo_by_date(context, taken_on):
    pending_selections = context["advice_response"].get("pending_selections", [])
    selection_id = pending_selections[0]["id"]
    option = f"Foto del {taken_on}"
    response = choose_selection(context["user_id"], selection_id, option)
    context["advice_response"] = response


@when("I confirm the photo deletion")
def confirm_photo_deletion(context):
    pending_confirmations = context["advice_response"].get("pending_confirmations", [])
    confirmation_id = pending_confirmations[0]["id"]
    accept_confirmation(context["user_id"], confirmation_id)


@when(parsers.parse('I cancel the photo deletion with reason "{reason}"'))
def cancel_photo_deletion(context, reason):
    pending_confirmations = context["advice_response"].get("pending_confirmations", [])
    confirmation_id = pending_confirmations[0]["id"]
    reject_confirmation(context["user_id"], confirmation_id, reason=reason)


@then(parsers.parse('bonsai "{bonsai_name}" should still have 1 photo'))
def assert_bonsai_still_has_one_photo(context, bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    photos = list_bonsai_photos(bonsai["id"])
    assert_that(len(photos), equal_to(1), f"Expected bonsai '{bonsai_name}' to still have 1 photo after cancellation")



# "I should receive an error indicating the bonsai does not exist" is defined in conftest.py
