import uuid

import pytest
from pytest_bdd import given, parsers

from cultivation_plan.planned_works_api import list_planned_works
from design_plan.development_plans_api import (
    create_development_plan,
    delete_development_plan,
    list_development_plans,
)
from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages, delete_wiki_page, write_wiki_page
from manage_species.species_api import delete_species_by_name, create_species


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-development-plan-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
        "wiki_pages_created": [],
        "pending_confirmations": [],
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for wiki_path in context.get("wiki_pages_created", []):
        delete_wiki_page(wiki_path)
    for bonsai_name in context["bonsai_created"]:
        bonsai_id = context["bonsai_ids"].get(bonsai_name)
        if bonsai_id:
            plans = list_development_plans(get, bonsai_id)
            for plan in plans:
                delete_development_plan(delete, plan["id"])
                delete_wiki_page(plan["wiki_path"])
        delete_bonsai_wiki_pages(bonsai_name)
        delete_bonsai_by_name(get, delete, bonsai_name)
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
    bonsai = create_bonsai(post, bonsai_name, species_id)
    context["bonsai_created"].append(bonsai_name)
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('"{bonsai_name}" has an analysis report in the wiki'))
def create_analysis_report(context, bonsai_name):
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    wiki_path = f"bonsai/{slug}/reports/test-analysis.md"
    write_wiki_page(
        wiki_path,
        f"# Analysis — {bonsai_name}\n\nVigor: high. No visible pests or diseases. Trunk developing well. "
        "Tree is healthy and suitable for training. Good ramification on lower branches.",
    )
    context["wiki_pages_created"].append(wiki_path)


@given(parsers.parse('"{bonsai_name}" has an analysis report from a previous year'))
def create_old_analysis_report(context, bonsai_name):
    import re
    from datetime import date
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    previous_year = date.today().year - 1
    wiki_path = f"bonsai/{slug}/reports/{previous_year}-06-15-analysis.md"
    write_wiki_page(
        wiki_path,
        f"# Analysis — {bonsai_name}\n\nVigor: high. No visible pests. Trunk developing well. "
        f"(Report from {previous_year} — may no longer reflect current state.)",
    )
    context["wiki_pages_created"].append(wiki_path)


@given(parsers.parse('"{bonsai_name}" has an active development plan with a future work on "{future_date}"'))
def create_active_plan_with_future_work(context, bonsai_name, future_date):
    bonsai_id = context["bonsai_ids"][bonsai_name]

    plan = create_development_plan(post, bonsai_id, "2026-06-01", "2099-12-31")
    plan_id = plan.get("id")

    planned_work_body = {
        "bonsai_id": bonsai_id,
        "development_plan_id": plan_id,
        "work_type": "defoliacion",
        "payload": {
            "technique_name": "defoliacion",
            "wiki_path": "techniques/defoliacion.md",
            "notes": "Test work",
        },
        "scheduled_date": future_date,
    }
    post(f"/api/bonsai/{bonsai_id}/planned-works", planned_work_body)
