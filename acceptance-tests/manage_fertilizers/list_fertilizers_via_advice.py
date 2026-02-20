from pytest_bdd import scenario, when, then, given, parsers

from http_client import accept_confirmation, advise


@scenario("../features/manage_fertilizers.feature", "List fertilizers via advice")
def test_list_fertilizers():
    return None


@given(parsers.parse('fertilizer "{name}" exists'))
def ensure_fertilizer_exists(context, name, external_stubs):
    response = advise(
        text=f"Da de alta el fertilizante {name}.",
        user_id=context["user_id"],
    )
    for confirmation in response.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when("I request the fertilizer list")
def request_fertilizer_list(context):
    response = advise(
        text="Qué fertilizantes tengo registrados?",
        user_id=context["user_id"],
    )
    context["response"] = response.get("text", "")


@then(parsers.parse('fertilizer list includes "{name}"'))
def assert_fertilizer_list(context, name):
    match = name in context.get("response", "")
    assert match, (
        f"Expected fertilizer list to include '{name}', got response: {context.get('response')}."
    )
