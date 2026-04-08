from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario("../features/manage_fertilizers.feature", "List fertilizers via advice")
def test_list_fertilizers():
    return None


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
