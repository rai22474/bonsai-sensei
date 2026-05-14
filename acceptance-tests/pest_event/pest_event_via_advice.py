from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/pest_event.feature", "Record a pest detection event for a bonsai")
def test_record_pest_detection_event():
    return None


@scenario("../features/pest_event.feature", "Cannot record a pest event for an unregistered pest")
def test_cannot_record_unregistered_pest_event():
    return None


@when(parsers.parse('I report detecting "{pest_name}" on "{bonsai_name}"'))
def report_pest_detection(context, pest_name, bonsai_name):
    response = advise(
        text=f"He detectado {pest_name} en mi bonsái {bonsai_name}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the pest detection")
def confirm_pest_detection(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(parsers.parse('bonsai "{bonsai_name}" should have a pest detection event for "{pest_name}"'))
def assert_pest_detection_event_recorded(context, bonsai_name, pest_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    matching = [
        event for event in events
        if event.get("event_type") == "pest_detection"
        and event.get("payload", {}).get("pest_name") == pest_name
    ]
    assert len(matching) > 0, (
        f"Expected a pest_detection event for bonsai '{bonsai_name}' "
        f"with pest '{pest_name}', but found events: {events}"
    )


@then("no confirmation should be pending for the pest detection")
def assert_no_pending_confirmation(context):
    pending = context.get("pending_confirmations", [])
    assert len(pending) == 0, (
        f"Expected no pending confirmations, but found: {pending}"
    )


@then(parsers.parse('bonsai "{bonsai_name}" should have no pest detection events'))
def assert_no_pest_detection_events(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    pest_events = [event for event in events if event.get("event_type") == "pest_detection"]
    assert len(pest_events) == 0, (
        f"Expected no pest_detection events for bonsai '{bonsai_name}', "
        f"but found: {pest_events}"
    )
