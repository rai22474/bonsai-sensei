import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from cultivation_plan.planned_works_api import list_planned_works
from design_plan.development_plans_api import create_development_plan, delete_development_plan, list_development_plans
from fertilization_plan.fertilization_plans_api import (
    create_fertilization_plan,
    delete_fertilization_plan,
    list_fertilization_plans,
)
from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages, delete_wiki_page, write_wiki_page
from manage_fertilizers.fertilizer_api import create_fertilizer, delete_fertilizer_by_name, find_fertilizer_by_name
from manage_species.species_api import delete_species_by_name, create_species

STUB_PORT = 8074


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-fertilization-plan-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "fertilizers_registered": [],
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
            plans = list_fertilization_plans(get, bonsai_id)
            for plan in plans:
                delete_wiki_page(plan["wiki_path"])
            dev_plans = list_development_plans(get, bonsai_id)
            for plan in dev_plans:
                delete_development_plan(delete, plan["id"])
                delete_wiki_page(plan["wiki_path"])
        delete_bonsai_wiki_pages(bonsai_name, user_id=context["user_id"])
        delete_bonsai_by_name(get, delete, bonsai_name, user_id=context["user_id"])
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)
    for name in context["fertilizers_registered"]:
        delete_fertilizer_by_name(delete, name, user_id=context["user_id"])


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {
            "answer": "Care guide for bonsai species.",
            "results": [],
        }
    )
    yield server
    server.stop()


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
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('fertilizer "{name}" is registered'))
def ensure_fertilizer_registered(context, name):
    create_fertilizer(post, name, user_id=context["user_id"])
    context["fertilizers_registered"].append(name)


@given(parsers.parse('"{bonsai_name}" has an active design plan with goal "{goal}"'))
def create_active_design_plan_with_wiki(context, bonsai_name, goal):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    user_id = context["user_id"]
    period_start = "2026-01-01"
    period_end = "2026-12-31"
    wiki_path = f"users/{user_id}/bonsai/{slug}/design-plans/{period_start[:7]}_to_{period_end[:7]}.md"
    create_development_plan(post, bonsai_id, period_start, period_end)
    write_wiki_page(
        wiki_path,
        f"# Plan de diseño — {bonsai_name}\n\n**Objetivo:** {goal}\n\n"
        "**Fase actual:** engorde de tronco. El árbol necesita fertilización nitrogenada alta durante la temporada de crecimiento.",
    )
    context["wiki_pages_created"].append(wiki_path)


@given(parsers.parse('"{bonsai_name}" has an active fertilization plan with a future work on "{future_date}"'))
def create_active_plan_with_future_work(context, bonsai_name, future_date):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    fertilizer_name = context["fertilizers_registered"][0]
    fertilizer = find_fertilizer_by_name(get, fertilizer_name, user_id=context["user_id"])

    plan = create_fertilization_plan(post, bonsai_id, "2026-06-01", "2099-12-31")
    plan_id = plan.get("id")

    planned_work_body = {
        "bonsai_id": bonsai_id,
        "plan_id": plan_id,
        "work_type": "fertilizer_application",
        "payload": {
            "fertilizer_id": fertilizer["id"],
            "fertilizer_name": fertilizer_name,
            "amount": "5g",
        },
        "scheduled_date": future_date,
    }
    post(f"/api/bonsai/{bonsai_id}/planned-works", planned_work_body)
