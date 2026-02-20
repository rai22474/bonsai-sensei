from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_fertilizers.fertilizer_api import find_fertilizer_by_name


@scenario("../features/manage_fertilizers.feature", "Update a fertilizer via advice")
def test_update_fertilizer():
    return None


@when(
    parsers.parse(
        'I request to update fertilizer "{name}" with recommended amount "{amount}"'
    )
)
def request_fertilizer_update(context, name, amount, external_stubs):
    response = advise(
        text=f"Actualiza el fertilizante {name} con dosis recomendada {amount}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the fertilizer update for "{name}"'))
def confirm_fertilizer_update(context, name, external_stubs):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(
    parsers.parse(
        'fertilizer "{name}" should have recommended amount "{amount}"'
    )
)
def assert_fertilizer_amount(name, amount):
    fertilizer = find_fertilizer_by_name(get, name)
    actual = fertilizer.get("recommended_amount") if fertilizer else None
    assert actual == amount, (
        f"Expected fertilizer '{name}' recommended amount to be '{amount}', got '{actual}'."
    )
