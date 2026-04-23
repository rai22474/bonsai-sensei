from pytest_bdd import scenario, given, when, then, parsers

from http_client import advise, reject_confirmation
from manage_bonsai.conftest import (
    create_bonsai_record,
    create_species_record,
    find_bonsai_by_name_api,
    get_species_record_id,
)


@scenario("../features/manage_bonsai.feature", "Cancel a bonsai deletion preserves the bonsai")
def test_cancel_bonsai_deletion():
    return None


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    create_species_record(context, name, scientific_name)


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = get_species_record_id(context, species_name)
    create_bonsai_record(context, bonsai_name, species_id)


@when(parsers.parse('I request to delete bonsai "{bonsai_name}"'))
def request_bonsai_delete(context, bonsai_name):
    response = advise(
        text=f"Elimina el bonsái {bonsai_name}.",
        user_id="bdd-cancel-bonsai",
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I cancel the deletion with reason "{reason}"'))
def cancel_deletion_with_reason(context, reason):
    for confirmation in context.get("pending_confirmations", []):
        reject_confirmation("bdd-cancel-bonsai", confirmation["id"], reason=reason)


@then(parsers.parse('bonsai "{bonsai_name}" should still exist'))
def assert_bonsai_still_exists(bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to still exist after cancellation."
