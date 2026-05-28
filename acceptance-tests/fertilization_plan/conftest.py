import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from cultivation_plan.planned_works_api import list_planned_works
from fertilization_plan.fertilization_plans_api import (
    create_fertilization_plan,
    delete_fertilization_plan,
    list_fertilization_plans,
)
from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages, delete_wiki_page
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
        "pending_confirmations": [],
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for bonsai_name in context["bonsai_created"]:
        bonsai_id = context["bonsai_ids"].get(bonsai_name)
        if bonsai_id:
            plans = list_fertilization_plans(get, bonsai_id)
            for plan in plans:
                delete_wiki_page(delete, plan["wiki_path"])
        delete_bonsai_wiki_pages(delete, bonsai_name)
        delete_bonsai_by_name(get, delete, bonsai_name)
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)
    for name in context["fertilizers_registered"]:
        delete_fertilizer_by_name(delete, name)


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
    bonsai = create_bonsai(post, bonsai_name, species_id)
    context["bonsai_created"].append(bonsai_name)
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('fertilizer "{name}" is registered'))
def ensure_fertilizer_registered(context, name):
    create_fertilizer(post, name)
    context["fertilizers_registered"].append(name)


@given(parsers.parse('"{bonsai_name}" has an active fertilization plan with a future work on "{future_date}"'))
def create_active_plan_with_future_work(context, bonsai_name, future_date):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    fertilizer_name = context["fertilizers_registered"][0]
    fertilizer = find_fertilizer_by_name(get, fertilizer_name)

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
