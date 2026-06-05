from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, choose_selection, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/pest_event.feature", "Record a pest detection event for a bonsai")
def test_record_pest_detection_event():
    return None


@scenario("../features/pest_event.feature", "Cannot record a pest event for an unregistered pest")
def test_cannot_record_unregistered_pest_event():
    return None


@scenario("../features/pest_event.feature", "Apply phytosanitary treatment linked to a pest detection event")
def test_apply_phytosanitary_linked_to_pest_event():
    return None


@when(parsers.parse('I apply "{product_name}" to "{bonsai_name}" with amount "{amount}"'))
def apply_phytosanitary_via_advice(context, product_name, bonsai_name, amount):
    response = advise(
        text=f"He aplicado {product_name} al bonsái {bonsai_name} con {amount}.",
        user_id=context["user_id"],
    )
    context["pending_selections"] = response.get("pending_selections", [])
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when(parsers.parse('I select the pest event for "{pest_name}" to link'))
def select_pest_event_to_link(context, pest_name):
    selections = context.get("pending_selections", [])
    assert selections, (
        f"Expected a pending selection to link the phytosanitary to a pest event, "
        f"but got none. The apply_phytosanitary tool may not have been called or "
        f"did not present a pest event selection."
    )
    selection_id = selections[0]["id"]
    options = selections[0].get("options", [])
    matching = next((opt for opt in options if pest_name.lower() in opt.lower()), None)
    assert matching is not None, f"No option containing '{pest_name}' found in: {options}"
    response = choose_selection(context["user_id"], selection_id, matching)
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the phytosanitary application")
def confirm_phytosanitary_application(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])



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


@then(parsers.parse('the phytosanitary application on "{bonsai_name}" should be linked to the pest detection event'))
def assert_phytosanitary_linked_to_pest_event(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)

    pest_detection_events = [event for event in events if event.get("event_type") == "pest_detection"]
    assert len(pest_detection_events) > 0, (
        f"Expected a pest_detection event for bonsai '{bonsai_name}', but found: {events}"
    )
    pest_event_id = pest_detection_events[0]["id"]

    phytosanitary_events = [event for event in events if event.get("event_type") == "phytosanitary_application"]
    linked_events = [
        event for event in phytosanitary_events
        if event.get("payload", {}).get("pest_event_id") == pest_event_id
    ]
    assert len(linked_events) > 0, (
        f"Expected a phytosanitary_application event linked to pest_event_id={pest_event_id}, "
        f"but found phytosanitary events: {phytosanitary_events}"
    )

