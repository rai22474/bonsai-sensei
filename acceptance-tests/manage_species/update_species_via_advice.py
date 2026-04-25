from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_species.species_api import find_species_by_name


@scenario("../features/manage_species.feature", "Update a species via advice")
def test_update_species_via_advice():
    return None


@when(
    parsers.parse(
        'I request to update species "{name}" scientific name to "{scientific_name}"'
    )
)
def request_species_update(context, name, scientific_name):
    response = advise(
        text=(
            "Actualiza la especie "
            f"{name} del registro de especies para que el nombre científico sea {scientific_name}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the update for species "{name}"'))
def confirm_species_update(context, name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(
    parsers.parse(
        'species "{name}" should have scientific name "{scientific_name}"'
    )
)
def assert_species_scientific_name(name, scientific_name):
    species = find_species_by_name(get, name)
    actual = None if species is None else species.get("scientific_name")
    assert actual == scientific_name, (
        f"Expected species '{name}' scientific name to be '{scientific_name}', got '{actual}'."
    )

