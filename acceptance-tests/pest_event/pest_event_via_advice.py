from pytest_bdd import scenario, when, then, parsers

from http_client import accept_confirmation, advise, choose_selection, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/pest_event.feature", "Record a pest detection event for a bonsai")
def test_record_pest_detection_event():
    return None


@scenario("../features/pest_event.feature", "Cannot record a pest event for an unregistered pest")
def test_cannot_record_unregistered_pest_event():
    return None


@scenario(
    "../features/pest_event.feature",
    "Record pest detection and apply phytosanitary treatment linked to pest event",
)
def test_record_pest_detection_and_linked_treatment():
    return None


@scenario(
    "../features/pest_event.feature",
    "After recording pest detection on bonsai with active phytosanitary plan, plan review is proposed",
)
def test_plan_review_proposed_after_pest_detection():
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
    context["pending_treatment_confirmations"] = []
    context["pending_plan_reviews"] = []
    context["pending_selections"] = []
    for confirmation in context.get("pending_confirmations", []):
        response = accept_confirmation(context["user_id"], confirmation["id"])
        context["pending_treatment_confirmations"].extend(
            response.get("pending_confirmations", [])
        )
        context["pending_plan_reviews"].extend(
            response.get("pending_plan_reviews", [])
        )
        context["pending_selections"].extend(
            response.get("pending_selections", [])
        )


@when("I confirm that I applied a treatment")
def confirm_applied_treatment(context):
    context["pending_selections"] = []
    for confirmation in context.get("pending_treatment_confirmations", []):
        response = accept_confirmation(context["user_id"], confirmation["id"])
        context["pending_selections"].extend(
            response.get("pending_selections", [])
        )


@when(parsers.parse('I select "{product_name}" as the treatment product'))
def select_treatment_product(context, product_name):
    for selection in context.get("pending_selections", []):
        choose_selection(context["user_id"], selection["id"], product_name)


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


@then(parsers.parse('bonsai "{bonsai_name}" should have a phytosanitary treatment linked to the pest detection'))
def assert_linked_phytosanitary_treatment(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    pest_events = [event for event in events if event.get("event_type") == "pest_detection"]
    treatment_events = [event for event in events if event.get("event_type") == "phytosanitary_application"]
    assert len(pest_events) > 0, f"Expected a pest_detection event but found none in: {events}"
    pest_event_id = pest_events[0]["id"]
    linked = [
        event for event in treatment_events
        if event.get("payload", {}).get("pest_event_id") == pest_event_id
    ]
    assert len(linked) > 0, (
        f"Expected a phytosanitary_application event linked to pest_event_id={pest_event_id}, "
        f"but found treatment events: {treatment_events}"
    )


@then("a phytosanitary plan review should be proposed")
def assert_plan_review_proposed(context):
    pending_reviews = context.get("pending_plan_reviews", [])
    assert len(pending_reviews) > 0, (
        f"Expected a pending plan review to be proposed after pest detection, but got none. "
        f"pending_plan_reviews={pending_reviews}"
    )
