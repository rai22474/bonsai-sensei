import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from http_client import delete, get, post
from manage_bonsai.bonsai_api import create_bonsai, delete_bonsai_by_name
from manage_species.species_api import create_species, delete_species_by_name

STUB_PORT = 8070


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-episodic-memory-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
        "wiki_paths_created": [],
    }


@pytest.fixture(autouse=True)
def reset_memory_watermark():
    post("/api/wiki/transcripts/wiki-keeper/watermark/reset")
    yield


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {"answer": "Información de plaga disponible.", "results": []}
    )
    yield server
    server.stop()


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for wiki_path in context["wiki_paths_created"]:
        try:
            delete(f"/api/wiki?path={wiki_path}")
        except Exception:
            pass
    for name in context["bonsai_created"]:
        delete_bonsai_by_name(get, delete, name)
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
    slug = re.sub(r"[^a-z0-9]+", "-", bonsai_name.lower()).strip("-")
    context["wiki_paths_created"].append(f"bonsai/{slug}/index.md")
