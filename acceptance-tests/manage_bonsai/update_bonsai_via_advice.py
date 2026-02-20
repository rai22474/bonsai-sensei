from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise
from manage_bonsai.conftest import (
    create_bonsai_record,
    create_species_record,
    find_bonsai_by_name_api,
    get_species_record_id,
)


@scenario("../features/manage_bonsai.feature", "Update a bonsai name via advice")
def test_update_bonsai():
    return None


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    create_species_record(context, name, scientific_name)


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = get_species_record_id(context, species_name)
    create_bonsai_record(context, bonsai_name, species_id)


@when(parsers.parse('I request to rename bonsai "{bonsai_name}" to "{new_name}"'))
def request_bonsai_rename(context, bonsai_name, new_name):
    response = advise(
        text=f"Renombra el bonsái {bonsai_name} a {new_name}.",
        user_id="bdd-bonsai",
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the bonsai update for "{bonsai_name}"'))
def confirm_bonsai_update(context, bonsai_name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation("bdd-bonsai", confirmation["id"])
    context["bonsai_created"].append(bonsai_name)


@then(parsers.parse('bonsai "{bonsai_name}" should exist'))
def assert_bonsai_exists(bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to exist after update."
