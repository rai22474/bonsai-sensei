from pytest_bdd import scenario, when, then, parsers

from cultivation_plan.planned_works_api import list_planned_works
from design_plan.development_plans_api import get_active_development_plan, list_development_plans
from http_client import accept_confirmation, accept_plan_review, advise, get, send_text_response
from manage_bonsai.bonsai_events_api import list_bonsai_events

_GENERIC_CLARIFICATION_ANSWER = (
    "El árbol está sano con buen vigor. Sin restricciones. Sin contexto adicional."
)


@scenario("../features/development_plan.feature", "Development plan requires a photo when only old reports exist")
def test_development_plan_requires_photo_when_only_old_reports():
    return None


@scenario("../features/development_plan.feature", "Development plan requires a photo or analysis report when none exists")
def test_development_plan_requires_photo_when_no_reports():
    return None


@scenario("../features/development_plan.feature", "Executing a design work records the development phase in history")
def test_execute_design_work_records_phase():
    return None


@scenario("../features/development_plan.feature", "Abandoning a development plan records a phase change event")
def test_abandon_records_phase_change_event():
    return None


@scenario("../features/development_plan.feature", "Propose and confirm a development plan")
def test_propose_and_confirm_development_plan():
    return None


@scenario("../features/development_plan.feature", "Abandon an active development plan")
def test_abandon_development_plan():
    return None


@when(parsers.parse('I execute the planned work for "{bonsai_name}" via advice'))
def execute_design_planned_work(context, bonsai_name):
    response = advise(
        text=f"Ejecuta el trabajo planificado para el bonsái {bonsai_name}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])
    context["pending_selections"] = response.get("pending_selections", [])
    for confirmation in context["pending_confirmations"]:
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse(
    'I request a development plan for "{bonsai_name}" as a "{development_path}" '
    'in phase "{current_phase}" targeting style "{target_style}" with goal "{design_goal}"'
))
def request_development_plan(context, bonsai_name, development_path, current_phase, target_style, design_goal):
    response = advise(
        text=(
            f"Quiero crear un plan de desarrollo para el bonsái {bonsai_name}. "
            f"Es un {development_path} en fase de {current_phase}. "
            f"El estilo objetivo es {target_style}. "
            f"Objetivo de diseño: {design_goal}. "
            f"Planifica del 2026-09-01 al 2027-08-31."
        ),
        user_id=context["user_id"],
    )
    context["last_advice_response"] = response
    context["received_text_question"] = bool(response.get("pending_text_questions"))
    while response.get("pending_text_questions"):
        response = send_text_response(context["user_id"], _GENERIC_CLARIFICATION_ANSWER)
        context["last_advice_response"] = response
        context["received_text_question"] = True
        if response.get("pending_plan_reviews"):
            break
    context["pending_confirmations"] = response.get("pending_confirmations", [])
    context["pending_plan_reviews"] = response.get("pending_plan_reviews", [])


@when(parsers.parse('I confirm the development plan for "{bonsai_name}"'))
def confirm_development_plan(context, bonsai_name):
    for plan_review in context.get("pending_plan_reviews", []):
        accept_plan_review(context["user_id"], plan_review["id"])
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I ask to abandon the development plan for "{bonsai_name}" because "{reason}"'))
def ask_to_abandon_plan(context, bonsai_name, reason):
    response = advise(
        text=f"Abandona el plan de desarrollo activo para el bonsái {bonsai_name}. Motivo: {reason}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the abandonment")
def confirm_abandonment(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(parsers.parse('"{bonsai_name}" should have an active development plan'))
def assert_active_plan_exists(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = get_active_development_plan(get, bonsai_id)
    assert plan is not None, (
        f"Expected '{bonsai_name}' to have an active development plan, but none found"
    )
    assert plan.get("status") == "active", (
        f"Expected plan status 'active', got '{plan.get('status')}'"
    )


@then(parsers.parse('"{bonsai_name}" should have planned works linked to the development plan'))
def assert_planned_works_linked_to_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = get_active_development_plan(get, bonsai_id)
    assert plan is not None, f"No active plan for '{bonsai_name}'"
    plan_id = plan["id"]

    works = list_planned_works(get, bonsai_id)
    linked = [work for work in works if work.get("development_plan_id") == plan_id]
    assert len(linked) > 0, (
        f"Expected planned works linked to development plan {plan_id} for '{bonsai_name}', "
        f"but none found. All works: {works}"
    )


@then(parsers.parse('"{bonsai_name}" should have no active development plan'))
def assert_no_active_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = get_active_development_plan(get, bonsai_id)
    assert plan is None, (
        f"Expected '{bonsai_name}' to have no active plan, but found: {plan}"
    )


@then("the agent should ask for a photo before starting the plan")
def assert_agent_asks_for_photo(context):
    asked_question = context.get("received_text_question", False)
    no_plan_created = get_active_development_plan(get, context["bonsai_ids"]["Kuromatsu"]) is None
    assert asked_question, (
        "Expected the agent to ask a question (requesting a photo) but no pending_text_questions "
        f"was ever received. Last response: {context.get('last_advice_response', {})}"
    )
    assert no_plan_created, (
        "Expected no development plan to be created when no analysis reports exist and "
        "user did not provide a photo, but an active plan was found."
    )


@then(parsers.parse('"{bonsai_name}" history should contain an event with development phase'))
def assert_event_has_development_phase(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    events_with_phase = [
        event for event in events
        if event.get("payload", {}).get("development_phase")
    ]
    assert len(events_with_phase) > 0, (
        f"Expected at least one event with 'development_phase' in payload for '{bonsai_name}', "
        f"but none found. Events: {events}"
    )


@then(parsers.parse('"{bonsai_name}" history should contain a phase_change event'))
def assert_phase_change_event_recorded(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    events = list_bonsai_events(get, bonsai_id)
    phase_change_events = [
        event for event in events
        if event.get("event_type") == "phase_change"
    ]
    assert len(phase_change_events) > 0, (
        f"Expected a 'phase_change' event for '{bonsai_name}' after abandoning the plan, "
        f"but none found. Events: {events}"
    )
    payload = phase_change_events[0].get("payload", {})
    assert payload.get("phase_abandoned"), (
        f"Expected 'phase_abandoned' in phase_change event payload, got: {payload}"
    )


@then(parsers.parse('"{bonsai_name}" should have no planned works linked to the abandoned plan'))
def assert_no_future_works_from_abandoned_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plans = list_development_plans(get, bonsai_id)
    abandoned = [plan for plan in plans if plan.get("status") == "abandoned"]
    assert len(abandoned) > 0, f"Expected at least one abandoned plan for '{bonsai_name}'"

    plan_id = abandoned[0]["id"]
    works = list_planned_works(get, bonsai_id)
    linked = [work for work in works if work.get("development_plan_id") == plan_id]
    assert len(linked) == 0, (
        f"Expected no planned works linked to abandoned plan {plan_id}, "
        f"but found: {linked}"
    )
