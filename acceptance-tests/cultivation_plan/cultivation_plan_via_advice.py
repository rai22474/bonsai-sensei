from datetime import date

from pytest_bdd import scenario, when, then, parsers

from cultivation_plan.planned_works_api import list_planned_works
from http_client import accept_confirmation, advise, get
from manage_bonsai.bonsai_events_api import list_bonsai_events


@scenario("../features/cultivation_plan.feature", "Plan a fertilization for a bonsai")
def test_plan_fertilization():
    return None


@scenario("../features/cultivation_plan.feature", "Ask about weekend planned works")
def test_ask_about_weekend_works():
    return None


@scenario("../features/cultivation_plan.feature", "Planning without a date suggests the next weekend")
def test_plan_without_date_suggests_weekend():
    return None


@scenario("../features/cultivation_plan.feature", "Replan removes an outdated planned fertilization")
def test_replan_removes_outdated_fertilization():
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


@when(
    parsers.parse(
        'I plan a fertilization of "{fertilizer_name}" with amount "{amount}" for "{bonsai_name}" without specifying a date'
    )
)
def plan_fertilization_without_date(context, fertilizer_name, bonsai_name, amount):
    response = advise(
        text=(
            f"Quiero planificar una fertilización con {fertilizer_name} "
            f"en cantidad de {amount} para el bonsái {bonsai_name}. "
            f"No tengo una fecha concreta en mente, elige la que consideres más adecuada."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I ask what I have planned for the weekend")
def ask_about_weekend_works(context):
    response = advise(
        text="¿Qué tengo planificado para este fin de semana?",
        user_id=context["user_id"],
    )
    context["response_text"] = response.get("text", "")


@when("I confirm the planned work")
def confirm_planned_work(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(
    parsers.parse(
        'I ask to remove the planned fertilization of "{fertilizer_name}" for "{bonsai_name}"'
    )
)
def ask_to_remove_planned_fertilization(context, fertilizer_name, bonsai_name):
    response = advise(
        text=(
            f"Por favor, elimina el trabajo planificado de fertilización con {fertilizer_name} "
            f"del plan del bonsái {bonsai_name}. Ya no es necesario."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


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


@then(parsers.parse('the response mentions "{expected_text}"'))
def assert_response_mentions(context, expected_text):
    response_text = context.get("response_text", "")
    assert expected_text in response_text, (
        f"Expected response to mention '{expected_text}', but got: {response_text}"
    )


@then(parsers.parse('the planned fertilization for "{bonsai_name}" is scheduled on a weekend day'))
def assert_planned_on_weekend(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    works = list_planned_works(get, bonsai_id)
    fertilization_works = [
        work for work in works if work.get("work_type") == "fertilizer_application"
    ]
    assert len(fertilization_works) > 0, (
        f"Expected at least one planned fertilization for bonsai '{bonsai_name}', "
        f"but found: {works}"
    )
    scheduled_date = date.fromisoformat(fertilization_works[0]["scheduled_date"])
    assert scheduled_date.weekday() in (5, 6), (
        f"Expected the planned fertilization for '{bonsai_name}' to be scheduled on a Saturday (5) "
        f"or Sunday (6), but got weekday {scheduled_date.weekday()} ({scheduled_date})"
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
