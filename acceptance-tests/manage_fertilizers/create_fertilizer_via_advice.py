from pytest_bdd import scenario, when, then, parsers

from http_client import advise, get
from manage_fertilizers.fertilizer_api import find_fertilizer_by_name


@scenario("../features/manage_fertilizers.feature", "Create a fertilizer via advice")
def test_create_fertilizer():
    return None


@when(parsers.parse('I request to register fertilizer "{name}"'))
def request_fertilizer_creation(context, name, external_stubs):
    advise(
        text=f"Da de alta el fertilizante {name}.",
        user_id=context["user_id"],
    )


@when(parsers.parse('I confirm the fertilizer creation for "{name}"'))
def confirm_fertilizer_creation(context, name, external_stubs):
    advise(
        text=f"Sí, confirma el alta del fertilizante {name}.",
        user_id=context["user_id"],
    )


@then(parsers.parse('fertilizer "{name}" should exist'))
def assert_fertilizer_exists(name):
    fertilizer = find_fertilizer_by_name(get, name)
    actual = fertilizer.get("name") if fertilizer else None
    assert actual == name, f"Expected fertilizer '{name}' to exist, got '{actual}'."
