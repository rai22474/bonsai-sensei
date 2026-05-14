import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_species.species_api import delete_species_by_name, create_species
from pest_event.pest_api import create_pest, delete_pest_by_name

STUB_PORT = 8076


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-pest-event-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "pests_registered": [],
        "bonsai_ids": {},
        "species_ids": {},
        "pest_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for name in context["pests_registered"]:
        delete_pest_by_name(delete, name)
    for name in context["bonsai_created"]:
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
