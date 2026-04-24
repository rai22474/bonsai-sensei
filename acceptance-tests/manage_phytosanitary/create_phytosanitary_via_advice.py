from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_phytosanitary.phytosanitary_api import (
    find_phytosanitary_by_name,
    list_phytosanitary,
)


@scenario("../features/manage_phytosanitary.feature", "Create a phytosanitary product via advice")
def test_create_phytosanitary():
    return None


@when(parsers.parse('I request to register phytosanitary product "{name}"'))
def request_phytosanitary_creation(context, name, external_stubs):
    response = advise(
        text=f"Da de alta el fitosanitario {name}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the phytosanitary creation for "{name}"'))
def confirm_phytosanitary_creation(context, name, external_stubs):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])
    context["phytosanitaries_created"].append(name)


@then(parsers.parse('phytosanitary product "{name}" should exist'))
def assert_phytosanitary_exists(name):
    phytosanitary = find_phytosanitary_by_name(get, name)
    items = list_phytosanitary(get)
    actual = phytosanitary.get("name") if phytosanitary else None
    assert (actual, len(items)) == (name, 1), (
        f"Expected phytosanitary '{name}' to exist and list size to be 1, "
        f"got name '{actual}' with list size {len(items)}."
    )


@then(parsers.parse('phytosanitary product "{name}" should have a wiki page'))
def assert_phytosanitary_has_wiki_page(name):
    phytosanitary = find_phytosanitary_by_name(get, name)
    wiki_path = (phytosanitary or {}).get("wiki_path")
    assert wiki_path, f"Expected phytosanitary '{name}' to have a wiki_path, got: {phytosanitary}"
    content = get(f"/api/wiki?path={wiki_path}").get("content", "")
    assert content, f"Expected wiki page at '{wiki_path}' to have content, got empty."
