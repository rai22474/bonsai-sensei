from pytest_bdd import scenario, given, when, then, parsers

from http_client import advise
from manage_bonsai.conftest import (
    create_bonsai_record,
    create_species_record,
    find_bonsai_by_name_api,
    get_species_record_id,
    delete_bonsai_by_name,
)


@scenario("../features/manage_bonsai.feature", "Delete a bonsai via advice")
def test_delete_bonsai():
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
    advise(
        text=f"Elimina el bonsái {bonsai_name}.",
        user_id="bdd-bonsai",
    )


@when(parsers.parse('I confirm the bonsai deletion for "{bonsai_name}"'))
def confirm_bonsai_delete(context, bonsai_name):
    advise(
        text=f"Sí, confirma la eliminación del bonsái {bonsai_name}.",
        user_id="bdd-bonsai",
    )


@then(parsers.parse('bonsai "{bonsai_name}" should not exist'))
def assert_bonsai_missing(bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is None, f"Expected bonsai '{bonsai_name}' to be deleted."
