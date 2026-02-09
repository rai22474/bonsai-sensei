from pytest_bdd import scenario, given, when, then, parsers

from http_client import advise
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
    advise(
        text=(
            f"Da de alta un bonsái llamado {bonsai_name} "
            f"de la especie {species_name} con id {species_id}."
        ),
        user_id="bdd-bonsai",
    )


@when(parsers.parse('I confirm the bonsai creation for "{bonsai_name}"'))
def confirm_bonsai_creation(context, bonsai_name):
    advise(
        text=f"Sí, confirma el alta del bonsái {bonsai_name}.",
        user_id="bdd-bonsai",
    )


@then(parsers.parse('bonsai "{bonsai_name}" should exist'))
def assert_bonsai_exists(bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to exist after creation."
