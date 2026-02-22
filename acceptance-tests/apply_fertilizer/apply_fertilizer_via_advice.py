from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/apply_fertilizer.feature", "Apply fertilizer to a bonsai")
def test_apply_fertilizer():
    return None


@scenario("../features/apply_fertilizer.feature", "Cannot apply an unregistered fertilizer to a bonsai")
def test_apply_unregistered_fertilizer():
    return None


@scenario("../features/apply_fertilizer.feature", "List fertilizer applications for a bonsai")
def test_list_fertilizer_applications():
    return None


@given(
    parsers.parse('"{fertilizer_name}" has been applied to "{bonsai_name}" with amount "{amount}"')
)
def apply_fertilizer_as_precondition(context, fertilizer_name, bonsai_name, amount):
    response = advise(
        text=(
            f"He aplicado el fertilizante {fertilizer_name} al bonsái {bonsai_name} "
            f"con una cantidad de {amount}."
        ),
        user_id=context["user_id"],
    )
    for confirmation in response.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(
    parsers.parse(
        'I report applying "{fertilizer_name}" fertilizer to "{bonsai_name}" with amount "{amount}"'
    )
)
def report_fertilizer_application(context, fertilizer_name, bonsai_name, amount):
    response = advise(
        text=(
            f"He aplicado el fertilizante {fertilizer_name} al bonsái {bonsai_name} "
            f"con una cantidad de {amount}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the fertilizer application")
def confirm_fertilizer_application(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I list the fertilizer applications for "{bonsai_name}"'))
def list_fertilizer_applications_for_bonsai(context, bonsai_name):
    response = advise(
        text=f"¿Qué fertilizantes se han aplicado al bonsái {bonsai_name}?",
        user_id=context["user_id"],
    )
    context["fertilizer_applications_response"] = response.get("text", "")


@then(
    parsers.parse(
        'bonsai "{bonsai_name}" should have a fertilizer application of "{fertilizer_name}" with amount "{amount}"'
    )
)
def assert_fertilizer_application_recorded(context, bonsai_name, fertilizer_name, amount):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    matching = [
        event for event in events
        if event.get("event_type") == "fertilizer_application"
        and event.get("payload", {}).get("fertilizer_name") == fertilizer_name
        and event.get("payload", {}).get("amount") == amount
    ]
    assert len(matching) > 0, (
        f"Expected a fertilizer_application event for bonsai '{bonsai_name}' "
        f"with fertilizer '{fertilizer_name}' and amount '{amount}', "
        f"but found events: {events}"
    )


@then("no confirmation should be pending for the fertilizer application")
def assert_no_pending_confirmation(context):
    pending = context.get("pending_confirmations", [])
    assert len(pending) == 0, (
        f"Expected no pending confirmations, but found: {pending}"
    )


@then(parsers.parse('bonsai "{bonsai_name}" should have no fertilizer application events'))
def assert_no_fertilizer_events(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    fertilizer_events = [
        event for event in events
        if event.get("event_type") == "fertilizer_application"
    ]
    assert len(fertilizer_events) == 0, (
        f"Expected no fertilizer_application events for bonsai '{bonsai_name}', "
        f"but found: {fertilizer_events}"
    )


@then(
    parsers.parse(
        'the list should contain a fertilizer application of "{fertilizer_name}" with amount "{amount}"'
    )
)
def assert_list_contains_application(context, fertilizer_name, amount):
    response_text = context.get("fertilizer_applications_response", "")
    assert fertilizer_name in response_text, (
        f"Expected response to mention '{fertilizer_name}', but got: {response_text}"
    )
    assert amount in response_text, (
        f"Expected response to mention amount '{amount}', but got: {response_text}"
    )
