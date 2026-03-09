from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, get
from judge import create_recommendation_metric
from manage_phytosanitary.phytosanitary_api import find_phytosanitary_by_name

AMOUNT_EQUIVALENCE_CRITERIA = (
    "The actual stored amount should convey the same dosage as the expected amount. "
    "Minor additions like 'de agua' that do not change the numeric value are acceptable."
)


@scenario("../features/manage_phytosanitary.feature", "Update a phytosanitary product via advice")
def test_update_phytosanitary():
    return None


@when(
    parsers.parse(
        'I request to update phytosanitary product "{name}" with recommended amount "{amount}"'
    )
)
def request_phytosanitary_update(context, name, amount, external_stubs):
    response = advise(
        text=f"Actualiza el fitosanitario {name} con dosis recomendada {amount}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I confirm the phytosanitary update for "{name}"'))
def confirm_phytosanitary_update(context, name, external_stubs):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(
    parsers.parse(
        'phytosanitary product "{name}" should have recommended amount "{amount}"'
    )
)
def assert_phytosanitary_amount(name, amount):
    phytosanitary = find_phytosanitary_by_name(get, name)
    actual = phytosanitary.get("recommended_amount") if phytosanitary else ""
    test_case = LLMTestCase(input=amount, actual_output=actual)
    metric = create_recommendation_metric("amount_equivalence", AMOUNT_EQUIVALENCE_CRITERIA)
    assert_test(test_case=test_case, metrics=[metric], run_async=False)
