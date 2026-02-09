from pytest_bdd import scenario, given, when, then, parsers

from http_client import advise, delete, get
from manage_species.species_api import delete_species_by_name, find_species_by_name


@scenario("../features/manage_species.feature", "Create a species via advice")
def test_create_species_via_advice():
    return None


@given(parsers.parse('no species named "{name}" exists'))
def ensure_species_absent(context, name, external_stubs):
    context["created"].append(name)
    delete_species_by_name(get, delete, name)


@when(
    parsers.parse(
        'I request to register species "{name}" with scientific name "{scientific_name}"'
    )
)
def request_species_creation(context, name, scientific_name):
    context["created"].append(name)
    advise(
        text=(
            "Da de alta la especie de bonsái "
            f"{name} con nombre científico {scientific_name}."
        ),
        user_id=context["user_id"],
    )


@when(
    parsers.parse(
        'I confirm the species creation for "{name}" with scientific name "{scientific_name}"'
    )
)
def confirm_species_creation(context, name, scientific_name):
    advise(
        text=(
            "Sí, confirma la creación de la especie "
            f"{name} con nombre científico {scientific_name}."
        ),
        user_id=context["user_id"],
    )


@then(parsers.parse('species "{name}" should exist'))
def assert_species_exists(name):
    species = find_species_by_name(get, name)
    assert species is not None, f"Expected species '{name}' to exist after creation."

