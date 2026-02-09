from pytest_bdd import scenario, when, then, given, parsers

from http_client import advise


@scenario("../features/manage_phytosanitary.feature", "List phytosanitary products via advice")
def test_list_phytosanitary():
    return None


@given(parsers.parse('phytosanitary product "{name}" exists'))
def ensure_phytosanitary_exists(context, name, external_stubs):
    advise(
        text=f"Da de alta el fitosanitario {name}.",
        user_id=context["user_id"],
    )
    advise(
        text=f"Sí, confirma el alta del fitosanitario {name}.",
        user_id=context["user_id"],
    )


@when("I request the phytosanitary list")
def request_phytosanitary_list(context):
    response = advise(
        text="Qué fitosanitarios tengo registrados?",
        user_id=context["user_id"],
    )
    context["response"] = response.get("response", "")


@then(parsers.parse('phytosanitary list includes "{name}"'))
def assert_phytosanitary_list(context, name):
    match = name in context.get("response", "")
    assert match, (
        f"Expected phytosanitary list to include '{name}', got response: {context.get('response')}."
    )
