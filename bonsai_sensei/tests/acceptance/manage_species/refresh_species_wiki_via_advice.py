from pytest_bdd import scenario, when, parsers

from http_client import accept_confirmation, advise


@scenario("../features/manage_species.feature", "Refresh species wiki via advice")
def test_refresh_species_wiki():
    return None


@when(parsers.parse('I request to refresh the wiki page for species "{name}" with instructions "{instructions}"'))
def request_species_wiki_refresh(context, name, instructions, external_stubs):
    response = advise(
        text=f"Actualiza la ficha wiki de la especie {name}. {instructions}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the wiki refresh for species "{name}"'))
def confirm_species_wiki_refresh(context, name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])

