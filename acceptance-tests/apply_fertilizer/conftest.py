import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, parsers

from http_client import accept_confirmation, advise, delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, find_bonsai_by_name
from manage_species.species_api import delete_species_by_name

STUB_PORT = 8070


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-fertilizer-apply-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for name in context["bonsai_created"]:
        delete_bonsai_by_name(get, delete, name)
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {
            "answer": "Ficha de uso disponible. Dosis recomendada: 2 ml por litro de agua.",
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
def ensure_fertilizer_registered(context, name, external_stubs):
    response = advise(
        text=f"Da de alta el fertilizante {name}.",
        user_id=context["user_id"],
    )
    for confirmation in response.get("pending_confirmations", []):
        accept_confirmation(context["user_id"], confirmation["id"])
