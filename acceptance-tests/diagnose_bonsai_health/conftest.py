import re
import uuid

import pytest
from pytest_bdd import given, parsers
from pytest_httpserver import HTTPServer

from http_client import delete, get, post, post_bonsai_photo
from manage_bonsai.bonsai_api import (
    create_bonsai,
    delete_bonsai_by_name as delete_bonsai_by_name_api_func,
    find_bonsai_by_name as find_bonsai_by_name_api_func,
)
from manage_species.species_api import (
    create_species,
    delete_species_by_name as delete_species_by_name_api_func,
    get_species_id,
)
from manage_bonsai_photos.conftest import MINIMAL_PNG

STUB_PORT = 8070


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json({
        "answer": (
            "Acer palmatum es una especie caducifolia muy popular en bonsái. "
            "Riego: abundante en verano, moderado en invierno; evitar encharcamiento."
        ),
        "results": [],
    })
    yield server
    server.stop()


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-diagnose-{uuid.uuid4().hex}",
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for name in context["bonsai_created"]:
        bonsai = find_bonsai_by_name_api_func(get, name)
        if bonsai:
            delete(f"/api/bonsai/{bonsai['id']}/photos")
        delete_bonsai_by_name_api_func(get, delete, name)
    for name in context["species_created"]:
        delete_species_by_name_api_func(get, delete, name)


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"][name] = species.get("id")


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = get_species_id(get, context, species_name)
    bonsai = create_bonsai(post, bonsai_name, species_id)
    context["bonsai_created"].append(bonsai_name)
    context["bonsai_ids"][bonsai_name] = bonsai.get("id")


@given(parsers.parse('bonsai "{bonsai_name}" has a photo taken on "{taken_on}"'))
def ensure_bonsai_has_photo_on_date(context, bonsai_name, taken_on):
    bonsai = find_bonsai_by_name_api_func(get, bonsai_name)
    post_bonsai_photo(bonsai["id"], MINIMAL_PNG, taken_on=taken_on)
