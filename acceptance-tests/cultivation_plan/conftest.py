import re
import uuid
from datetime import date, timedelta

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from cultivation_plan.planned_works_api import create_planned_work
from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name
from manage_fertilizers.fertilizer_api import create_fertilizer, delete_fertilizer_by_name, find_fertilizer_by_name
from manage_species.species_api import delete_species_by_name

STUB_PORT = 8073


def _next_saturday() -> date:
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-cultivation-plan-{uuid.uuid4().hex}",
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
    for name in context["bonsai_created"]:
        delete_bonsai_by_name(get, delete, name)
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
    from manage_species.species_api import create_species
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"][name] = species.get("id")


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    from manage_bonsai.bonsai_api import create_bonsai
    species_id = context["species_ids"][species_name]
    bonsai = create_bonsai(post, bonsai_name, species_id)
    context["bonsai_created"].append(bonsai_name)
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('fertilizer "{name}" is registered'))
def ensure_fertilizer_registered(context, name):
    create_fertilizer(post, name)
    context["fertilizers_registered"].append(name)


@given(
    parsers.parse(
        '"{bonsai_name}" has a planned fertilization of "{fertilizer_name}" with amount "{amount}" on "{scheduled_date}"'
    )
)
def create_planned_fertilization_as_precondition(
    context, bonsai_name, fertilizer_name, amount, scheduled_date
):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    fertilizer = find_fertilizer_by_name(get, fertilizer_name)
    payload = {
        "fertilizer_id": fertilizer["id"],
        "fertilizer_name": fertilizer_name,
        "amount": amount,
    }
    create_planned_work(post, bonsai_id, "fertilizer_application", payload, scheduled_date)


@given(
    parsers.parse(
        '"{bonsai_name}" has a planned fertilization of "{fertilizer_name}" with amount "{amount}" for next Saturday'
    )
)
def create_planned_fertilization_for_next_saturday(
    context, bonsai_name, fertilizer_name, amount
):
    bonsai_id = context["bonsai_ids"][bonsai_name]
    fertilizer = find_fertilizer_by_name(get, fertilizer_name)
    payload = {
        "fertilizer_id": fertilizer["id"],
        "fertilizer_name": fertilizer_name,
        "amount": amount,
    }
    create_planned_work(
        post, bonsai_id, "fertilizer_application", payload, _next_saturday().isoformat()
    )
