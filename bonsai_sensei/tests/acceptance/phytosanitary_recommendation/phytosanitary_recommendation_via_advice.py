from pytest_bdd import scenario, when, then, parsers

from http_client import advise


@scenario(
    "../features/phytosanitary_recommendation.feature",
    "Ask for phytosanitary advice with no products in catalog returns online recommendations",
)
def test_phytosanitary_advice_online_when_no_products():
    return None


@when(parsers.parse('I ask for phytosanitary advice for "{bonsai_name}" against "{pest_name}"'))
def ask_for_phytosanitary_advice(context, bonsai_name, pest_name):
    response = advise(
        text=f"¿Qué producto fitosanitario me recomiendas para tratar {pest_name} en mi bonsái {bonsai_name}?",
        user_id=context["user_id"],
    )
    context["advice_response"] = response.get("text", "")


@then("the response should contain phytosanitary recommendations")
def assert_response_contains_recommendations(context, external_stubs):
    response_text = context.get("advice_response", "")
    assert len(response_text) > 50, (
        f"Expected a substantive recommendation response (>50 chars), got: '{response_text}'"
    )
    assert len(external_stubs.log) > 0, (
        "Expected Tavily search to be called (online search stub not hit). "
        "The tool did not perform a web search."
    )
