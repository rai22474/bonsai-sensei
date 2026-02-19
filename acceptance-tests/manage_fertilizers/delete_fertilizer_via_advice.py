from pytest_bdd import scenario, when, then, parsers

from http_client import advise, get
from manage_fertilizers.fertilizer_api import find_fertilizer_by_name


@scenario("../features/manage_fertilizers.feature", "Delete a fertilizer via advice")
def test_delete_fertilizer():
    return None


@when(parsers.parse('I request to delete fertilizer "{name}"'))
def request_fertilizer_deletion(context, name, external_stubs):
    advise(
        text=f"Elimina el fertilizante {name}.",
        user_id=context["user_id"],
    )


@when(parsers.parse('I confirm the fertilizer deletion for "{name}"'))
def confirm_fertilizer_deletion(context, name, external_stubs):
    advise(
        text="Aceptar",
        user_id=context["user_id"],
    )


@then(parsers.parse('fertilizer "{name}" should not exist'))
def assert_fertilizer_missing(name):
    fertilizer = find_fertilizer_by_name(get, name)
    assert fertilizer is None, f"Expected fertilizer '{name}' to be deleted."
