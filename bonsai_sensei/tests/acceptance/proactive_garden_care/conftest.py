from datetime import date, datetime, timedelta, timezone

import pytest
from pytest_bdd import given, parsers

from design_plan.development_plans_api import delete_development_plan, list_development_plans
from fertilization_plan.fertilization_plans_api import delete_fertilization_plan, list_fertilization_plans
from http_client import delete, get, post, put
from manage_bonsai.bonsai_api import create_bonsai, delete_bonsai_by_name
from manage_bonsai.bonsai_events_api import record_bonsai_event
from manage_species.species_api import create_species, delete_species_by_name

TEST_USER_ID = "weekend-reminder-test-user"
STUB_PORT = 8075


def _next_saturday() -> date:
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


@pytest.fixture
def context():
    return {
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for bonsai_name in context["bonsai_created"]:
        bonsai_id = context.get("bonsai_ids", {}).get(bonsai_name)
        if bonsai_id:
            for plan in list_fertilization_plans(get, bonsai_id):
                delete_fertilization_plan(delete, plan["id"])
            for plan in list_development_plans(get, bonsai_id):
                delete_development_plan(delete, plan["id"])
        delete_bonsai_by_name(get, delete, bonsai_name)
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)
    delete(f"/api/users/{TEST_USER_ID}/settings")


@given(parsers.parse('user "{user_id}" has chat id "{chat_id}" registered'))
def register_user_with_chat_id(context, user_id, chat_id):
    put(f"/api/users/{user_id}/settings", {"telegram_chat_id": chat_id})


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"] = context.get("species_ids", {})
    context["species_ids"][name] = species.get("id")


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = context["species_ids"][species_name]
    bonsai = create_bonsai(post, bonsai_name, species_id)
    context["bonsai_created"].append(bonsai_name)
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('"{bonsai_name}" has an outdated fertilization plan'))
def create_outdated_fertilization_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    two_months_ago = (date.today() - timedelta(days=60)).isoformat()
    post(f"/api/bonsai/{bonsai_id}/fertilization-plans", {
        "bonsai_id": bonsai_id,
        "period_start": two_months_ago,
        "period_end": (date.today() + timedelta(days=60)).isoformat(),
        "status": "active",
        "wiki_path": f"bonsai/test/plans/{bonsai_id}-outdated.md",
        "goal": "engorde de tronco",
        "created_at": two_months_ago,
    })


@given(parsers.parse('"{bonsai_name}" has a newer active design plan'))
def create_newer_design_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    post(f"/api/bonsai/{bonsai_id}/development-plans", {
        "bonsai_id": bonsai_id,
        "development_path": "planton",
        "current_phase": "refinamiento",
        "target_style": "moyogi",
        "design_goal": "refinamiento de ápice",
        "period_start": date.today().isoformat(),
        "period_end": (date.today() + timedelta(days=365)).isoformat(),
        "status": "active",
        "wiki_path": f"bonsai/test/design-plans/{bonsai_id}-newer.md",
    })


@given(parsers.parse('"{bonsai_name}" has a recent unlinked pest detection for "{pest_name}"'))
def create_unlinked_pest_detection(context, bonsai_name, pest_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    record_bonsai_event(
        post_func=post,
        bonsai_id=bonsai_id,
        event_type="pest_detection",
        payload={"pest_name": pest_name},
    )


@given(parsers.parse('"{bonsai_name}" has an active fertilization plan'))
def create_active_fertilization_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    post(f"/api/bonsai/{bonsai_id}/fertilization-plans", {
        "bonsai_id": bonsai_id,
        "period_start": date.today().isoformat(),
        "period_end": (date.today() + timedelta(days=120)).isoformat(),
        "status": "active",
        "wiki_path": f"bonsai/test/plans/{bonsai_id}-active.md",
    })


@given(parsers.parse('"{bonsai_name}" has a recently abandoned fertilization plan due to disease'))
def create_abandoned_fertilization_plan_due_to_disease(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    post(f"/api/bonsai/{bonsai_id}/fertilization-plans", {
        "bonsai_id": bonsai_id,
        "period_start": (date.today() - timedelta(days=30)).isoformat(),
        "period_end": (date.today() + timedelta(days=90)).isoformat(),
        "status": "abandoned",
        "abandonment_reason": "disease_pause: araña roja",
        "abandoned_at": datetime.now(timezone.utc).isoformat(),
        "wiki_path": f"bonsai/test/plans/{bonsai_id}-abandoned.md",
    })


@given(parsers.parse('"{bonsai_name}" has a fertilization planned for next Saturday'))
def plan_fertilization_for_next_saturday(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    saturday = _next_saturday()
    post(
        f"/api/bonsai/{bonsai_id}/planned-works",
        {
            "work_type": "fertilizer_application",
            "payload": {"fertilizer_name": "Generic", "amount": "5 ml"},
            "scheduled_date": saturday.isoformat(),
        },
    )
