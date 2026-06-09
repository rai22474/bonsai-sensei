from pytest_bdd import scenario, when, then, parsers

from cultivation_plan.planned_works_api import list_planned_works
from fertilization_plan.fertilization_plans_api import get_active_fertilization_plan, list_fertilization_plans
from http_client import accept_confirmation, accept_plan_review, advise, choose_selection, get, send_text_response

_GENERIC_CLARIFICATION_ANSWER = (
    "Crecimiento activo. Sin preferencia de fertilizante. Sin contexto adicional."
)


@scenario("../features/fertilization_plan.feature", "Propose and confirm a fertilization plan")
def test_propose_and_confirm_fertilization_plan():
    return None


@scenario("../features/fertilization_plan.feature", "Fertilization plan uses active design plan as context")
def test_fertilization_plan_uses_active_design_plan():
    return None


@scenario("../features/fertilization_plan.feature", "Abandon an active fertilization plan")
def test_abandon_fertilization_plan():
    return None


@when(parsers.parse('I request a fertilization plan for "{bonsai_name}" from "{start_date}" to "{end_date}"'))
def request_fertilization_plan(context, bonsai_name, start_date, end_date):
    response = advise(
        text=(
            f"Quiero un plan de fertilización para el bonsái {bonsai_name} "
            f"para el periodo del {start_date} al {end_date}. "
            f"Usa los fertilizantes que tengo disponibles."
        ),
        user_id=context["user_id"],
    )
    if response.get("pending_selections"):
        selection_id = response["pending_selections"][0]["id"]
        response = choose_selection(context["user_id"], selection_id, "Plan de fertilización")
    while response.get("pending_text_questions"):
        response = send_text_response(context["user_id"], _GENERIC_CLARIFICATION_ANSWER)
        if response.get("pending_plan_reviews"):
            break
    context["plan_proposal_response"] = response.get("text", "")
    context["pending_confirmations"] = response.get("pending_confirmations", [])
    context["pending_plan_reviews"] = response.get("pending_plan_reviews", [])


@when(parsers.parse('I confirm the fertilization plan for "{bonsai_name}"'))
def confirm_fertilization_plan(context, bonsai_name):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])
    for plan_review in context.get("pending_plan_reviews", []):
        accept_plan_review(context["user_id"], plan_review["id"])


@when(parsers.parse('I ask to abandon the fertilization plan for "{bonsai_name}" because "{reason}"'))
def ask_to_abandon_plan(context, bonsai_name, reason):
    response = advise(
        text=f"Abandona el plan de fertilización activo para el bonsái {bonsai_name}. Motivo: {reason}.",
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the abandonment")
def confirm_abandonment(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@then(parsers.parse('"{bonsai_name}" should have an active fertilization plan'))
def assert_active_plan_exists(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = get_active_fertilization_plan(get, bonsai_id)
    assert plan is not None, (
        f"Expected '{bonsai_name}' to have an active fertilization plan, but none found"
    )
    assert plan.get("status") == "active", (
        f"Expected plan status 'active', got '{plan.get('status')}'"
    )


@then(parsers.parse('"{bonsai_name}" should have planned works linked to the fertilization plan'))
def assert_planned_works_linked_to_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = get_active_fertilization_plan(get, bonsai_id)
    assert plan is not None, f"No active plan for '{bonsai_name}'"
    plan_id = plan["id"]

    works = list_planned_works(get, bonsai_id)
    linked = [work for work in works if work.get("plan_id") == plan_id]
    assert len(linked) > 0, (
        f"Expected planned works linked to plan {plan_id} for '{bonsai_name}', "
        f"but none found. All works: {works}"
    )


@then(parsers.parse('"{bonsai_name}" should have no active fertilization plan'))
def assert_no_active_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = get_active_fertilization_plan(get, bonsai_id)
    assert plan is None, (
        f"Expected '{bonsai_name}' to have no active plan, but found: {plan}"
    )


@then(parsers.parse('"{bonsai_name}" should have no planned works linked to the abandoned plan'))
def assert_no_future_works_from_abandoned_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plans = list_fertilization_plans(get, bonsai_id)
    abandoned = [plan for plan in plans if plan.get("status") == "abandoned"]
    assert len(abandoned) > 0, f"Expected at least one abandoned plan for '{bonsai_name}'"

    plan_id = abandoned[0]["id"]
    works = list_planned_works(get, bonsai_id)
    linked = [work for work in works if work.get("plan_id") == plan_id]
    assert len(linked) == 0, (
        f"Expected no planned works linked to abandoned plan {plan_id}, "
        f"but found: {linked}"
    )
