import re
import uuid

import pytest
from hamcrest import assert_that, empty, equal_to
from pytest_bdd import given, then, parsers
from pytest_httpserver import HTTPServer

from http_client import delete, get, post, post_bonsai_photo
from manage_bonsai.bonsai_api import (
    create_bonsai,
    delete_bonsai_by_name as delete_bonsai_by_name_api_func,
    find_bonsai_by_name as find_bonsai_by_name_api_func,
)
from manage_species.species_api import create_species, delete_species_by_name as delete_species_by_name_api_func, get_species_id

STUB_PORT = 8070

MINIMAL_PNG = bytes([
    137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
    0, 0, 0, 1, 0, 0, 0, 1, 8, 2, 0, 0, 0, 144, 119, 83, 222, 0,
    0, 0, 12, 73, 68, 65, 84, 120, 156, 99, 248, 207, 192, 0, 0, 3,
    1, 1, 0, 201, 254, 146, 239, 0, 0, 0, 0, 73, 69, 78, 68, 174,
    66, 96, 130,
])


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {
            "answer": (
                "Acer palmatum es una especie caducifolia muy popular en bonsái. "
                "Riego: abundante en verano, moderado en invierno; evitar encharcamiento."
            ),
            "results": [],
        }
    )
    yield server
    server.stop()


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-photos-{uuid.uuid4().hex}",
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


def create_species_record(context: dict, name: str, scientific_name: str) -> dict:
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"][name] = species.get("id")
    return species


def create_bonsai_record(context: dict, name: str, species_id: int) -> dict:
    bonsai = create_bonsai(post, name, species_id)
    context["bonsai_created"].append(name)
    context["bonsai_ids"][name] = bonsai.get("id")
    return bonsai


def find_bonsai_by_name_api(name: str) -> dict | None:
    return find_bonsai_by_name_api_func(get, name)


def get_species_record_id(context: dict, name: str) -> int:
    return get_species_id(get, context, name)


def list_bonsai_photos(bonsai_id: int) -> list:
    return get(f"/api/bonsai/{bonsai_id}/photos") or []


def create_bonsai_photo_via_api(bonsai_id: int, photo_bytes: bytes, taken_on: str | None = None) -> dict:
    return post_bonsai_photo(bonsai_id, photo_bytes, taken_on=taken_on)


def delete_bonsai_photo_via_api(bonsai_id: int, photo_id: int) -> None:
    delete(f"/api/bonsai/{bonsai_id}/photos/{photo_id}")


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name):
    create_species_record(context, name, scientific_name)


@given(parsers.parse('a bonsai named "{bonsai_name}" exists for species "{species_name}"'))
def ensure_bonsai_exists(context, bonsai_name, species_name):
    species_id = get_species_record_id(context, species_name)
    create_bonsai_record(context, bonsai_name, species_id)


@given(parsers.parse('bonsai "{bonsai_name}" has a photo taken on "{taken_on}"'))
def ensure_bonsai_has_photo_on_date(context, bonsai_name, taken_on):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    create_bonsai_photo_via_api(bonsai["id"], MINIMAL_PNG, taken_on=taken_on)


@given(parsers.parse('no bonsai named "{bonsai_name}" exists'))
def ensure_bonsai_does_not_exist(context, bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    if bonsai:
        delete(f"/api/bonsai/{bonsai['id']}")


@then(parsers.parse('bonsai "{bonsai_name}" should have 1 photo'))
def assert_bonsai_has_one_photo(context, bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    assert bonsai is not None, f"Expected bonsai '{bonsai_name}' to exist"
    photos = list_bonsai_photos(bonsai["id"])
    assert_that(len(photos), equal_to(1), f"Expected bonsai '{bonsai_name}' to have 1 photo")


@then(parsers.parse('bonsai "{bonsai_name}" should have 2 photos'))
def assert_bonsai_has_two_photos(context, bonsai_name):
    bonsai = find_bonsai_by_name_api(bonsai_name)
    photos = list_bonsai_photos(bonsai["id"])
    assert_that(len(photos), equal_to(2), f"Expected bonsai '{bonsai_name}' to have 2 photos")


@then("I should receive an error indicating the bonsai does not exist")
def assert_bonsai_not_found_error(context):
    response = context.get("advice_response", {})
    pending_interactions = response.get("pending_confirmations", []) + response.get("pending_selections", [])
    assert_that(pending_interactions, empty(), "Expected no pending interaction when bonsai does not exist")
