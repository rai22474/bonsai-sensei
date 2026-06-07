import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from cultivation_plan.planned_works_api import list_planned_works
from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages, delete_wiki_page
from manage_phytosanitary.phytosanitary_api import create_phytosanitary, delete_phytosanitary_by_name, find_phytosanitary_by_name
from manage_species.species_api import delete_species_by_name, create_species
from phytosanitary_plan.phytosanitary_plans_api import (
    create_phytosanitary_plan,
    delete_phytosanitary_plan,
    list_phytosanitary_plans,
)

STUB_PORT = 8075


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-phytosanitary-plan-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "phytosanitaries_registered": [],
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
            plans = list_phytosanitary_plans(get, bonsai_id)
            for plan in plans:
                delete_wiki_page(plan["wiki_path"])
        delete_bonsai_wiki_pages(bonsai_name, user_id=context["user_id"])
        delete_bonsai_by_name(get, delete, bonsai_name, user_id=context["user_id"])
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)
    for name in context["phytosanitaries_registered"]:
        delete_phytosanitary_by_name(delete, name, user_id=context["user_id"])


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


@given(parsers.parse('phytosanitary product "{name}" is registered'))
def ensure_phytosanitary_registered(context, name):
    create_phytosanitary(post, name, user_id=context["user_id"])
    context["phytosanitaries_registered"].append(name)


@given(parsers.parse('"{bonsai_name}" has an active phytosanitary plan with a future treatment on "{future_date}"'))
def create_active_plan_with_future_treatment(context, bonsai_name, future_date):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    phytosanitary_name = context["phytosanitaries_registered"][0]
    phytosanitary = find_phytosanitary_by_name(get, phytosanitary_name, user_id=context["user_id"])

    plan = create_phytosanitary_plan(post, bonsai_id, "2026-06-01", "2099-12-31")
    plan_id = plan.get("id")

    planned_work_body = {
        "bonsai_id": bonsai_id,
        "phytosanitary_plan_id": plan_id,
        "work_type": "phytosanitary_application",
        "payload": {
            "phytosanitary_id": phytosanitary["id"],
            "phytosanitary_name": phytosanitary_name,
            "amount": "2ml/L",
        },
        "scheduled_date": future_date,
    }
    post(f"/api/bonsai/{bonsai_id}/planned-works", planned_work_body)
