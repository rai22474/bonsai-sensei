from pytest_bdd import scenario, given, when, then, parsers
from hamcrest import assert_that, not_none, contains_string

from http_client import accept_confirmation, advise, choose_selection
from manage_bonsai.conftest import (
    create_species_record,
    find_bonsai_by_name_api,
)
from manage_bonsai.wiki_api import get_wiki_page
from bonsai_sensei.domain.services.garden.nursery.bonsai_index_page import build_bonsai_wiki_path


@scenario("../features/manage_bonsai.feature", "Create a bonsai via advice")
def test_create_bonsai():
    return None


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    create_species_record(context, name, scientific_name)


@when(parsers.parse('I request to register bonsai "{bonsai_name}" for species "{species_name}"'))
def request_bonsai_creation(context, bonsai_name, species_name):
    response = advise(
        text=f"Da de alta un bonsái llamado {bonsai_name} de la especie {species_name}.",
        user_id=context["user_id"],
    )
    if response.get("pending_selections"):
        selection_id = response["pending_selections"][0]["id"]
        response = choose_selection(context["user_id"], selection_id, species_name)
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the bonsai creation for "{bonsai_name}"'))
def confirm_bonsai_creation(context, bonsai_name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])
    if bonsai_name not in context["bonsai_created"]:
        context["bonsai_created"].append(bonsai_name)


@then(parsers.parse('bonsai "{bonsai_name}" should exist'))
def assert_bonsai_exists(context, bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name, user_id=context["user_id"])
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to exist after creation."


@then(parsers.parse('the wiki index page for bonsai "{bonsai_name}" should exist with species "{species_name}"'))
def assert_wiki_index_exists(context, bonsai_name, species_name):
    wiki_path = build_bonsai_wiki_path(bonsai_name, context["user_id"])
    page = get_wiki_page(wiki_path)
    assert_that(page, not_none(), f"Expected wiki index page at {wiki_path} to exist")
    assert_that(page["content"], contains_string(bonsai_name), "Wiki index should contain the bonsai name")
    assert_that(page["content"], contains_string(species_name), "Wiki index should contain the species name")
