import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages
from manage_bonsai.bonsai_events_api import record_bonsai_event
from manage_phytosanitary.phytosanitary_api import create_phytosanitary, delete_phytosanitary_by_name
from manage_species.species_api import delete_species_by_name, create_species
from pest_event.pest_api import create_pest, delete_pest_by_name

STUB_PORT = 8070


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-pest-event-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "pests_registered": [],
        "phytosanitaries_registered": [],
        "phytosanitary_plan_ids": [],
        "bonsai_ids": {},
        "species_ids": {},
        "pest_ids": {},
        "phytosanitary_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for plan_id in context["phytosanitary_plan_ids"]:
        try:
            delete(f"/api/phytosanitary-plans/{plan_id}")
        except Exception:
            pass
    for name in context["pests_registered"]:
        delete_pest_by_name(delete, name)
    for name in context["phytosanitaries_registered"]:
        delete_phytosanitary_by_name(delete, name)
    for name in context["bonsai_created"]:
        delete_bonsai_wiki_pages(delete, name)
        delete_bonsai_by_name(get, delete, name)
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {"answer": "Ficha de plaga disponible.", "results": []}
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


@given(parsers.parse('pest "{name}" is registered in the catalog'))
def ensure_pest_registered(context, name):
    pest = create_pest(post, name)
    context["pests_registered"].append(name)
    context["pest_ids"][name] = pest.get("id")


@given(parsers.parse('phytosanitary product "{name}" is registered'))
def ensure_phytosanitary_registered(context, name):
    phytosanitary = create_phytosanitary(post, name)
    context["phytosanitaries_registered"].append(name)
    context["phytosanitary_ids"][name] = phytosanitary.get("id")


@given(parsers.parse('bonsai "{bonsai_name}" has a recent pest detection event for "{pest_name}"'))
def ensure_recent_pest_detection_event(context, bonsai_name, pest_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    pest_id = context["pest_ids"][pest_name]
    record_bonsai_event(
        post_func=post,
        bonsai_id=bonsai_id,
        event_type="pest_detection",
        payload={"pest_id": pest_id, "pest_name": pest_name},
    )


@given(parsers.parse('bonsai "{bonsai_name}" has an active phytosanitary plan'))
def ensure_active_phytosanitary_plan(context, bonsai_name):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    plan = post(
        f"/api/bonsai/{bonsai_id}/phytosanitary-plans",
        {
            "bonsai_id": bonsai_id,
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
            "status": "active",
            "wiki_path": "plans/test-phytosanitary.md",
        },
    )
    context["phytosanitary_plan_ids"].append(plan["id"])
