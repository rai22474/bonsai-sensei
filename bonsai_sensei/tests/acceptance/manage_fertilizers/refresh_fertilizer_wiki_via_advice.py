from pytest_bdd import scenario, when, parsers

from http_client import accept_confirmation, advise


@scenario("../features/manage_fertilizers.feature", "Refresh fertilizer wiki via advice")
def test_refresh_fertilizer_wiki():
    return None


@when(parsers.parse('I request to refresh the wiki page for fertilizer "{name}" with instructions "{instructions}"'))
def request_fertilizer_wiki_refresh(context, name, instructions, external_stubs):
    response = advise(
        text=f"Actualiza la ficha wiki del fertilizante {name}. {instructions}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the wiki refresh for fertilizer "{name}"'))
def confirm_fertilizer_wiki_refresh(context, name, external_stubs):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])
