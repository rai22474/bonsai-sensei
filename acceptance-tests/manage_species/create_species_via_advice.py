from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise, choose_selection, delete, get
from manage_species.species_api import delete_species_by_name, find_species_by_name


@scenario("../features/manage_species.feature", "Create a species via advice")
def test_create_species_via_advice():
    return None


@scenario("../features/manage_species.feature", "Care guide is generated as wiki page after species creation")
def test_care_guide_generated_as_wiki_page():
    return None


@scenario("../features/manage_species.feature", "User is asked to choose variety when species name is ambiguous")
def test_user_asked_to_choose_variety_when_ambiguous():
    return None


@given(parsers.parse('no species named "{name}" exists'))
def ensure_species_absent(context, name):
    context["created"].append(name)
    delete_species_by_name(get, delete, name)


@when(
    parsers.parse(
        'I request to register species "{name}" with scientific name "{scientific_name}"'
    )
)
def request_species_creation(context, name, scientific_name, external_stubs):
    context["created"].append(name)
    response = advise(
        text=(
            "Da de alta la especie de bonsái "
            f"{name} con nombre científico {scientific_name}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(
    parsers.parse(
        'I confirm the species creation for "{name}" with scientific name "{scientific_name}"'
    )
)
def confirm_species_creation(context, name, scientific_name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I request to register ambiguous species "{name}"'))
def request_ambiguous_species(context, name, external_stubs_ambiguous):
    context["created"].append(name)
    response = advise(
        text=f"Da de alta la especie de bonsái {name}.",
        user_id=context["user_id"],
    )
    context["pending_selections"] = response.get("pending_selections", [])


@when(parsers.parse('I choose scientific name "{scientific_name}" from the selection'))
def select_scientific_name(context, scientific_name):
    for selection in context.get("pending_selections", []):
        response = choose_selection(context["user_id"], selection["id"], scientific_name)
        if response:
            context["pending_confirmations"] = response.get("pending_confirmations", [])


@then(parsers.parse('species "{name}" should exist'))
def assert_species_exists(name):
    species = find_species_by_name(get, name)
    assert species is not None, f"Expected species '{name}' to exist after creation."


@then(parsers.parse('species "{name}" should exist with scientific name "{scientific_name}"'))
def assert_species_exists_with_scientific_name(name, scientific_name):
    species = find_species_by_name(get, name)
    assert species is not None, f"Expected species '{name}' to exist after creation."
    assert species.get("scientific_name") == scientific_name, (
        f"Expected scientific name '{scientific_name}', got '{species.get('scientific_name')}'"
    )



