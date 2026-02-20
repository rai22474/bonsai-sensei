from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise
from manage_bonsai.conftest import (
    create_species_record,
    find_bonsai_by_name_api,
    get_species_record_id,
)


@scenario("../features/manage_bonsai.feature", "Create a bonsai via advice")
def test_create_bonsai():
    return None


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    create_species_record(context, name, scientific_name)


@when(parsers.parse('I request to register bonsai "{bonsai_name}" for species "{species_name}"'))
def request_bonsai_creation(context, bonsai_name, species_name):
    species_id = get_species_record_id(context, species_name)
    response = advise(
        text=(
            f"Da de alta un bonsái llamado {bonsai_name} "
            f"de la especie {species_name} con id {species_id}."
        ),
        user_id="bdd-bonsai",
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the bonsai creation for "{bonsai_name}"'))
def confirm_bonsai_creation(context, bonsai_name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation("bdd-bonsai", confirmation["id"])


@then(parsers.parse('bonsai "{bonsai_name}" should exist'))
def assert_bonsai_exists(bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to exist after creation."
