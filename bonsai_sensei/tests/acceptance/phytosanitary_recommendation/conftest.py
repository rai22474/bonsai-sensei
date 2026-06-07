import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from http_client import delete, get, post
from manage_bonsai.bonsai_api import delete_bonsai_by_name, create_bonsai
from manage_bonsai.wiki_api import delete_bonsai_wiki_pages
from manage_species.species_api import delete_species_by_name, create_species

STUB_PORT = 8070

_STUB_SEARCH_ANSWER = (
    "Para tratar araña roja en bonsai se recomienda Aceite de Neem (2 ml/L) o Abamectina (1 ml/L). "
    "El Aceite de Neem actúa como insecticida y acaricida orgánico. "
    "Aplicar en el envés de las hojas, evitar horas de sol directo."
)


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-phytosanitary-rec-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for name in context["bonsai_created"]:
        delete_bonsai_wiki_pages(name, user_id=context["user_id"])
        delete_bonsai_by_name(get, delete, name, user_id=context["user_id"])
    for name in context["species_created"]:
        delete_species_by_name(get, delete, name)


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {"answer": _STUB_SEARCH_ANSWER, "results": []}
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
