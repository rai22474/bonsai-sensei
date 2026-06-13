import re
import uuid
from datetime import date

import pytest
from pytest_bdd import given, parsers

from http_client import delete, get, post
from manage_bonsai.bonsai_api import create_bonsai, delete_bonsai_by_name
from manage_bonsai.wiki_api import delete_wiki_page
from manage_species.species_api import create_species, delete_species_by_name


def _bonsai_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-work-refinement-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
        "development_plan_ids": [],
        "refinement_wiki_paths": [],
        "gallery_photo_count_before": 0,
        "sent_session_photo": False,
        "pending_selections": [],
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for wiki_path in context.get("refinement_wiki_paths", []):
        delete_wiki_page(wiki_path)
    for plan_id in context.get("development_plan_ids", []):
        try:
            delete(f"/api/development-plans/{plan_id}")
        except Exception:
            pass
    for bonsai_name in context["bonsai_created"]:
        bonsai_id = context["bonsai_ids"].get(bonsai_name)
        if bonsai_id:
            try:
                delete(f"/api/bonsai/{bonsai_id}/photos")
            except Exception:
                pass
        delete_bonsai_by_name(get, delete, bonsai_name, user_id=context["user_id"])
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"][name] = species.get("id")


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = context["species_ids"][species_name]
    bonsai = create_bonsai(post, bonsai_name, species_id, user_id=context["user_id"])
    context["bonsai_created"].append(bonsai_name)
    bonsai_id = bonsai.get("id")
    context["bonsai_ids"][bonsai_name] = bonsai_id
    photos = get(f"/api/bonsai/{bonsai_id}/photos") or []
    context["gallery_photo_count_before"] = len(photos)


@given(parsers.parse('"{bonsai_name}" has an active development plan with a "{work_type}" planned on "{scheduled_date}"'))
def create_plan_with_planned_work(context, bonsai_name, work_type, scheduled_date):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    user_id = context["user_id"]
    slug = _bonsai_slug(bonsai_name)
    period_start = "2026-06-01"
    period_end = "2027-05-31"
    wiki_path = f"users/{user_id}/bonsai/{slug}/design-plans/{period_start[:7]}_to_{period_end[:7]}.md"

    plan = post(f"/api/bonsai/{bonsai_id}/development-plans", {
        "bonsai_id": bonsai_id,
        "development_path": "planton",
        "current_phase": "engorde",
        "target_style": "moyogi",
        "design_goal": "Test plan for refinement acceptance test",
        "period_start": period_start,
        "period_end": period_end,
        "status": "active",
        "wiki_path": wiki_path,
        "created_at": date.today().isoformat(),
    })
    context["development_plan_ids"].append(plan["id"])
    context["plan_wiki_path"] = wiki_path
    context["work_type_slug"] = work_type.lower().replace(" ", "-")

    post(f"/api/bonsai/{bonsai_id}/planned-works", {
        "bonsai_id": bonsai_id,
        "development_plan_id": plan["id"],
        "work_type": work_type,
        "payload": {"technique_name": work_type, "notes": "test"},
        "scheduled_date": scheduled_date,
    })
