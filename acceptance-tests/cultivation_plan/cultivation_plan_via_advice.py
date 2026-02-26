from pytest_bdd import scenario, when, then, parsers

from cultivation_plan.planned_works_api import list_planned_works
from http_client import accept_confirmation, advise, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/cultivation_plan.feature", "Plan a fertilization for a bonsai")
def test_plan_fertilization():
    return None


@scenario("../features/cultivation_plan.feature", "Execute a planned fertilization")
def test_execute_planned_fertilization():
    return None


@when(
    parsers.parse(
        'I plan a fertilization of "{fertilizer_name}" with amount "{amount}" for "{bonsai_name}" on "{scheduled_date}"'
    )
)
def plan_fertilization_via_advice(context, fertilizer_name, bonsai_name, amount, scheduled_date):
    response = advise(
        text=(
            f"Quiero planificar una fertilización con {fertilizer_name} "
            f"en cantidad de {amount} para el bonsái {bonsai_name} "
            f"para el {scheduled_date}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the planned work")
def confirm_planned_work(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I report executing planned work for "{bonsai_name}" and "{fertilizer_name}"'))
def report_executing_planned_work(context, bonsai_name, fertilizer_name):
    response = advise(
        text=(
            f"He ejecutado el trabajo planificado de fertilización "
            f"con {fertilizer_name} para el bonsái {bonsai_name}."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the execution")
def confirm_execution(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(
    parsers.parse(
        '"{bonsai_name}" should have a planned fertilization of "{fertilizer_name}" on "{scheduled_date}"'
    )
)
def assert_planned_fertilization_exists(context, bonsai_name, fertilizer_name, scheduled_date):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    works = list_planned_works(get, bonsai_id)
    matching = [
        work for work in works
        if work.get("work_type") == "fertilizer_application"
        and work.get("payload", {}).get("fertilizer_name") == fertilizer_name
        and work.get("scheduled_date") == scheduled_date
    ]
    assert len(matching) > 0, (
        f"Expected a planned fertilizer_application for bonsai '{bonsai_name}' "
        f"with fertilizer '{fertilizer_name}' on '{scheduled_date}', "
        f"but found planned works: {works}"
    )


@then(
    parsers.parse(
        'bonsai "{bonsai_name}" should have a fertilizer_application event for "{fertilizer_name}"'
    )
)
def assert_fertilizer_event_recorded(context, bonsai_name, fertilizer_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    matching = [
        event for event in events
        if event.get("event_type") == "fertilizer_application"
        and event.get("payload", {}).get("fertilizer_name") == fertilizer_name
    ]
    assert len(matching) > 0, (
        f"Expected a fertilizer_application event for bonsai '{bonsai_name}' "
        f"with fertilizer '{fertilizer_name}', but found events: {events}"
    )


@then(
    parsers.parse('"{bonsai_name}" should have no pending planned works for "{fertilizer_name}"')
)
def assert_no_pending_planned_works(context, bonsai_name, fertilizer_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    works = list_planned_works(get, bonsai_id)
    matching = [
        work for work in works
        if work.get("payload", {}).get("fertilizer_name") == fertilizer_name
    ]
    assert len(matching) == 0, (
        f"Expected no planned works for '{fertilizer_name}' for bonsai '{bonsai_name}', "
        f"but found: {matching}"
    )
