from pytest_bdd import scenario, when, then, parsers

from http_client import advise, get
from manage_phytosanitary.phytosanitary_api import (
    find_phytosanitary_by_name,
    list_phytosanitary,
)


@scenario("../features/manage_phytosanitary.feature", "Create a phytosanitary product via advice")
def test_create_phytosanitary():
    return None


@when(parsers.parse('I request to register phytosanitary product "{name}"'))
def request_phytosanitary_creation(context, name, external_stubs):
    advise(
        text=f"Da de alta el fitosanitario {name}.",
        user_id=context["user_id"],
    )


@when(parsers.parse('I confirm the phytosanitary creation for "{name}"'))
def confirm_phytosanitary_creation(context, name, external_stubs):
    advise(
        text=f"Sí, confirma el alta del fitosanitario {name}.",
        user_id=context["user_id"],
    )


@then(parsers.parse('phytosanitary product "{name}" should exist'))
def assert_phytosanitary_exists(name):
    phytosanitary = find_phytosanitary_by_name(get, name)
    items = list_phytosanitary(get)
    actual = phytosanitary.get("name") if phytosanitary else None
    assert (actual, len(items)) == (name, 1), (
        f"Expected phytosanitary '{name}' to exist and list size to be 1, "
        f"got name '{actual}' with list size {len(items)}."
    )
