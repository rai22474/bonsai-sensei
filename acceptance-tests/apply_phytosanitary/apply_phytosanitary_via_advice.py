from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise, get, post
from manage_bonsai.bonsai_events_api import list_bonsai_events, record_bonsai_event


@scenario("../features/apply_phytosanitary.feature", "Apply phytosanitary treatment to a bonsai")
def test_apply_phytosanitary():
    return None


@scenario("../features/apply_phytosanitary.feature", "Cannot apply an unregistered phytosanitary product to a bonsai")
def test_apply_unregistered_phytosanitary():
    return None


@scenario("../features/apply_phytosanitary.feature", "List phytosanitary treatments for a bonsai")
def test_list_phytosanitary_treatments():
    return None


@given(
    parsers.parse('"{phytosanitary_name}" phytosanitary treatment has been applied to "{bonsai_name}" with amount "{amount}"')
)
def apply_phytosanitary_as_precondition(context, phytosanitary_name, bonsai_name, amount):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    phytosanitary_id = context["phytosanitary_ids"][phytosanitary_name]
    record_bonsai_event(
        post_func=post,
        bonsai_id=bonsai_id,
        event_type="phytosanitary_application",
        payload={"phytosanitary_id": phytosanitary_id, "phytosanitary_name": phytosanitary_name, "amount": amount},
    )


@when(
    parsers.parse(
        'I report applying "{phytosanitary_name}" phytosanitary treatment to "{bonsai_name}" with amount "{amount}"'
    )
)
def report_phytosanitary_application(context, phytosanitary_name, bonsai_name, amount):
    response = advise(
        text=(
            f"He aplicado el fitosanitario {phytosanitary_name} al bonsái {bonsai_name} "
            f"con una cantidad de {amount}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the phytosanitary application")
def confirm_phytosanitary_application(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I list the phytosanitary treatments for "{bonsai_name}"'))
def list_phytosanitary_treatments_for_bonsai(context, bonsai_name):
    response = advise(
        text=f"¿Qué tratamientos fitosanitarios se han aplicado al bonsái {bonsai_name}?",
        user_id=context["user_id"],
    )
    context["phytosanitary_treatments_response"] = response.get("text", "")


@then(
    parsers.parse(
        'bonsai "{bonsai_name}" should have a phytosanitary application of "{phytosanitary_name}" with amount "{amount}"'
    )
)
def assert_phytosanitary_application_recorded(context, bonsai_name, phytosanitary_name, amount):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    matching = [
        event for event in events
        if event.get("event_type") == "phytosanitary_application"
        and event.get("payload", {}).get("phytosanitary_name") == phytosanitary_name
        and event.get("payload", {}).get("amount") == amount
    ]
    assert len(matching) > 0, (
        f"Expected a phytosanitary_application event for bonsai '{bonsai_name}' "
        f"with product '{phytosanitary_name}' and amount '{amount}', "
        f"but found events: {events}"
    )


@then("no confirmation should be pending for the phytosanitary application")
def assert_no_pending_confirmation(context):
    pending = context.get("pending_confirmations", [])
    assert len(pending) == 0, (
        f"Expected no pending confirmations, but found: {pending}"
    )


@then(parsers.parse('bonsai "{bonsai_name}" should have no phytosanitary application events'))
def assert_no_phytosanitary_events(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    phytosanitary_events = [
        event for event in events
        if event.get("event_type") == "phytosanitary_application"
    ]
    assert len(phytosanitary_events) == 0, (
        f"Expected no phytosanitary_application events for bonsai '{bonsai_name}', "
        f"but found: {phytosanitary_events}"
    )


@then(parsers.parse('the treatment list should contain "{phytosanitary_name}" with amount "{amount}"'))
def assert_treatment_list_contains(context, phytosanitary_name, amount):
    response_text = context.get("phytosanitary_treatments_response", "")
    assert phytosanitary_name in response_text, (
        f"Expected response to mention '{phytosanitary_name}', but got: {response_text}"
    )
    assert amount in response_text, (
        f"Expected response to mention amount '{amount}', but got: {response_text}"
    )
