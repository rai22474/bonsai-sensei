from pytest_bdd import scenario, when, then, parsers

from http_client import advise, get
from manage_phytosanitary.phytosanitary_api import find_phytosanitary_by_name


@scenario("../features/manage_phytosanitary.feature", "Delete a phytosanitary product via advice")
def test_delete_phytosanitary():
    return None


@when(parsers.parse('I request to delete phytosanitary product "{name}"'))
def request_phytosanitary_deletion(context, name, external_stubs):
    advise(
        text=f"Elimina el fitosanitario {name}.",
        user_id=context["user_id"],
    )


@when(parsers.parse('I confirm the phytosanitary deletion for "{name}"'))
def confirm_phytosanitary_deletion(context, name, external_stubs):
    advise(
        text="Aceptar",
        user_id=context["user_id"],
    )


@then(parsers.parse('phytosanitary product "{name}" should not exist'))
def assert_phytosanitary_missing(name):
    phytosanitary = find_phytosanitary_by_name(get, name)
    assert phytosanitary is None, f"Expected phytosanitary '{name}' to be deleted."
