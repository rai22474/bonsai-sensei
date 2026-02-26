from pytest_bdd import scenario, when, then, parsers

from cultivation_plan.planned_works_api import list_planned_works
from http_client import accept_confirmation, advise, get


@scenario(
    "../features/cultivation_plan_context.feature",
    "Plan fertilization selects from available registered fertilizers",
)
def test_plan_uses_registered_fertilizer():
    return None


@scenario(
    "../features/cultivation_plan_context.feature",
    "Cultivation agent can consult bonsai event history",
)
def test_agent_consults_event_history():
    return None


@when(
    parsers.parse(
        'I ask to plan a fertilization for "{bonsai_name}" on "{scheduled_date}" without specifying a fertilizer'
    )
)
def plan_fertilization_without_specifying_fertilizer(context, bonsai_name, scheduled_date):
    response = advise(
        text=(
            f"Quiero planificar una fertilización para el bonsái {bonsai_name} "
            f"para el {scheduled_date}. No tengo preferencia por el fertilizante, "
            f"elige el que esté disponible."
        ),
        user_id=context["user_id"],
    )
    context["pending_confirmations"] = response.get("pending_confirmations", [])


@when("I confirm the planned work")
def confirm_planned_work(context):
    for confirmation in context.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])


@when(parsers.parse('I ask about recent fertilization treatments for "{bonsai_name}"'))
def ask_about_recent_fertilization(context, bonsai_name):
    response = advise(
        text=f"¿Cuáles han sido los últimos tratamientos de fertilización del bonsái {bonsai_name}?",
        user_id=context["user_id"],
    )
    context["response_text"] = response.get("text", "")


@then(parsers.parse('"{bonsai_name}" should have a planned fertilization using "{fertilizer_name}"'))
def assert_planned_fertilization_uses_fertilizer(context, bonsai_name, fertilizer_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    works = list_planned_works(get, bonsai_id)
    matching = [
        work for work in works
        if work.get("work_type") == "fertilizer_application"
        and work.get("payload", {}).get("fertilizer_name") == fertilizer_name
    ]
    assert len(matching) > 0, (
        f"Expected a planned fertilizer_application using '{fertilizer_name}' for bonsai '{bonsai_name}', "
        f"but found planned works: {works}"
    )


@then(parsers.parse('the response mentions "{fertilizer_name}"'))
def assert_response_mentions_fertilizer(context, fertilizer_name):
    response_text = context.get("response_text", "")
    assert fertilizer_name in response_text, (
        f"Expected response to mention '{fertilizer_name}', but got: {response_text}"
    )
