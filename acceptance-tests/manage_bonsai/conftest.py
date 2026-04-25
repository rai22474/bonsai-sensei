import re

import pytest
from pytest_httpserver import HTTPServer

from http_client import delete, get, post, put
from manage_bonsai.bonsai_api import (
    create_bonsai,
    delete_bonsai_by_name as delete_bonsai_by_name_api_func,
    find_bonsai_by_name as find_bonsai_by_name_api_func,
    update_bonsai,
)
from manage_species.species_api import create_species, get_species_id


STUB_PORT = 8070


@pytest.fixture(autouse=True)
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {
            "answer": (
                "Acer palmatum es una especie caducifolia muy popular en bonsái. "
                "Riego: abundante en verano, moderado en invierno; evitar encharcamiento. "
                "Luz: semisombra, proteger del sol directo en verano. "
                "Suelo: mezcla drenante de akadama y pomice en proporción 60/40. "
                "Poda: formación en otoño; pinzado de brotes tiernos en primavera. "
                "Plagas habituales: pulgones y cochinilla; tratar con aceite de neem. "
                "Cuidados por estación: en primavera fertilizar cada 15 días; en verano riego diario; "
                "en otoño reducir fertilización; en invierno proteger de heladas fuertes."
            ),
            "results": [],
        }
    )
    yield server
    server.stop()


@pytest.fixture
def context():
    return {
        "bonsai_created": [],
        "species_created": [],
        "bonsai_ids": {},
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_records(context):
    yield
    for name in context["bonsai_created"]:
        delete_bonsai_by_name_api_func(get, delete, name)


def create_species_record(context: dict, name: str, scientific_name: str) -> dict:
    species = create_species(post, name, scientific_name)
    context["species_created"].append(name)
    context["species_ids"][name] = species.get("id")
    return species


def get_species_record_id(context: dict, name: str) -> int:
    return get_species_id(get, context, name)


def create_bonsai_record(context: dict, name: str, species_id: int) -> dict:
    bonsai = create_bonsai(post, name, species_id)
    context["bonsai_created"].append(name)
    context["bonsai_ids"][name] = bonsai.get("id")
    return bonsai


def find_bonsai_by_name_api(name: str) -> dict | None:
    return find_bonsai_by_name_api_func(get, name)


def delete_bonsai_by_name(name: str) -> None:
    delete_bonsai_by_name_api_func(get, delete, name)


def update_bonsai_record(bonsai_id: int, payload: dict) -> dict:
    return update_bonsai(put, bonsai_id, payload)
