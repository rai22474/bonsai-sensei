from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_phytosanitary.phytosanitary_api import find_phytosanitary_by_name


@scenario("../features/manage_phytosanitary.feature", "Update phytosanitary recommended amount via advice")
def test_update_phytosanitary_recommended_amount():
    return None


@when(parsers.parse('I request to update phytosanitary product "{name}" with recommended amount "{amount}"'))
def request_phytosanitary_update(context, name, amount, external_stubs):
    response = advise(
        text=f"Actualiza la cantidad recomendada del fitosanitario {name} a {amount}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the phytosanitary update for "{name}"'))
def confirm_phytosanitary_update(context, name, external_stubs):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(parsers.parse('phytosanitary product "{name}" should have recommended amount "{amount}"'))
def assert_phytosanitary_recommended_amount(name, amount):
    phytosanitary = find_phytosanitary_by_name(get, name)
    actual = (phytosanitary or {}).get("recommended_amount")
    assert actual == amount, \
        f"Expected phytosanitary '{name}' recommended_amount to be '{amount}', got: '{actual}'"
