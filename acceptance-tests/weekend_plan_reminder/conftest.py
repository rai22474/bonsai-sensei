from datetime import date, timedelta

import pytest
from pytest_bdd import given, parsers

from http_client import delete, get, post, put
from manage_bonsai.bonsai_api import create_bonsai, delete_bonsai_by_name
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
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for name in context["bonsai_created"]:
        delete_bonsai_by_name(get, delete, name)
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
    context["bonsai_ids"] = context.get("bonsai_ids", {})
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


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
