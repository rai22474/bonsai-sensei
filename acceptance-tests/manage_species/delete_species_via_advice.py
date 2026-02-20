from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise, delete, get, post
from manage_species.species_api import (
    create_species,
    delete_species_by_name,
    find_species_by_name,
)


@scenario("../features/manage_species.feature", "Delete a species via advice")
def test_delete_species_via_advice():
    return None


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name, external_stubs):
    delete_species_by_name(get, delete, name)
    species = create_species(post, name, scientific_name)
    context["created"].append(name)
    context["species_ids"][name] = species.get("id")


@when(parsers.parse('I request to delete species "{name}"'))
def request_species_delete(context, name):
    response = advise(
        text=f"Borra la especie {name} del registro de especies.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the deletion for species "{name}"'))
def confirm_species_delete(context, name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(parsers.parse('species "{name}" should not exist'))
def assert_species_missing(name):
    species = find_species_by_name(get, name)
    assert species is None, f"Expected species '{name}' to be deleted."

