import uuid

from pytest_bdd import scenario, given, when, then, parsers

from http_client import accept_confirmation, advise, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/transplant.feature", "Record a transplant for a bonsai")
def test_record_transplant():
    return None


@scenario("../features/transplant.feature", "List transplants for a bonsai")
def test_list_transplants():
    return None


@given(
    parsers.parse('a transplant for "{bonsai_name}" has been recorded with pot size "{pot_size}", pot type "{pot_type}" and substrate "{substrate}"')
)
def record_transplant_as_precondition(context, bonsai_name, pot_size, pot_type, substrate):
    setup_user_id = f"setup-{uuid.uuid4().hex}"
    response = advise(
        text=(
            f"He trasplantado el bonsái {bonsai_name} a una maceta de {pot_type} de {pot_size} "
            f"con substrato de {substrate}."
        ),
        user_id=setup_user_id,
    )
    for confirmation in response.get("pending_confirmations", []):
        accept_confirmation(setup_user_id, confirmation["id"])


@when(
    parsers.parse(
        'I report a transplant for "{bonsai_name}" with pot size "{pot_size}", pot type "{pot_type}" and substrate "{substrate}"'
    )
)
def report_transplant(context, bonsai_name, pot_size, pot_type, substrate):
    response = advise(
        text=(
            f"He trasplantado el bonsái {bonsai_name} a una maceta de {pot_type} de {pot_size} "
            f"con substrato de {substrate}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the transplant")
def confirm_transplant(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I list the transplants for "{bonsai_name}"'))
def list_transplants_for_bonsai(context, bonsai_name):
    response = advise(
        text=f"¿Qué trasplantes se han realizado al bonsái {bonsai_name}?",
        user_id=context["user_id"],
    )
    context["transplants_response"] = response.get("text", "")


@then(
    parsers.parse(
        'bonsai "{bonsai_name}" should have a transplant event with pot size "{pot_size}", pot type "{pot_type}" and substrate "{substrate}"'
    )
)
def assert_transplant_event_recorded(context, bonsai_name, pot_size, pot_type, substrate):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    matching = [
        event for event in events
        if event.get("event_type") == "transplant"
        and event.get("payload", {}).get("pot_size") == pot_size
        and event.get("payload", {}).get("pot_type") == pot_type
        and event.get("payload", {}).get("substrate") == substrate
    ]
    assert len(matching) > 0, (
        f"Expected a transplant event for bonsai '{bonsai_name}' "
        f"with pot size '{pot_size}', pot type '{pot_type}' and substrate '{substrate}', "
        f"but found events: {events}"
    )


@then(parsers.parse('the list should mention "{text}"'))
def assert_list_mentions(context, text):
    response_text = context.get("transplants_response", "")
    assert text in response_text, (
        f"Expected response to mention '{text}', but got: {response_text}"
    )
