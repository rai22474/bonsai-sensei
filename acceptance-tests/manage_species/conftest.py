import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, then, parsers

from http_client import delete, get, post
from manage_species.species_api import create_species, delete_species_by_name, find_species_by_name

STUB_PORT = 8070


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-species-{uuid.uuid4().hex}",
        "created": [],
        "species_ids": {},
    }


@pytest.fixture(autouse=True)
def cleanup_species(context):
    yield
    for name in context["created"]:
        delete_species_by_name(get, delete, name)


@given(parsers.parse('species "{name}" exists with scientific name "{scientific_name}"'))
def ensure_species_exists(context, name, scientific_name, external_stubs):
    delete_species_by_name(get, delete, name)
    species = create_species(post, name, scientific_name)
    context["created"].append(name)
    context["species_ids"][name] = species.get("id")


@then(parsers.parse('the wiki page for species "{name}" should contain watering information'))
def assert_wiki_page_has_watering(name):
    species = find_species_by_name(get, name)
    wiki_path = (species or {}).get("wiki_path")
    assert wiki_path, f"Expected species '{name}' to have a wiki_path, got: {species}"
    content = get(f"/api/wiki?path={wiki_path}").get("content", "")
    assert "## Riego" in content or "watering" in content.lower(), (
        f"Expected wiki page for '{name}' to contain watering section, got: {content[:300]}"
    )


@pytest.fixture
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(
        re.compile(r"/api/v1/plants/search.*")
    ).respond_with_json(
        {"data": [{"scientific_name": "Ficus retusa"}]}
    )
    server.expect_request("/search").respond_with_json(
        {
            "answer": (
                "Ficus retusa es una especie tropical de bonsái muy popular. "
                "Riego: abundante en verano, moderado en invierno; evitar encharcamiento. "
                "Luz: pleno sol o semisombra, mínimo 4 horas de luz directa al día. "
                "Suelo: mezcla drenante de akadama y volcánica en proporción 60/40. "
                "Poda: formación en primavera y verano; pinzado continuo durante el crecimiento. "
                "Plagas habituales: cochinilla, araña roja y pulgones; tratar con aceite de neem. "
                "Cuidados por estación: en primavera fertilizar cada 15 días; en verano riego diario; "
                "en otoño reducir fertilización; en invierno proteger de heladas."
            ),
            "results": [],
        }
    )
    yield server
    server.stop()


@pytest.fixture
def external_stubs_ambiguous():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(
        re.compile(r"/api/v1/plants/search.*")
    ).respond_with_json(
        {"data": [
            {"scientific_name": "Juniperus chinensis"},
            {"scientific_name": "Juniperus communis"},
            {"scientific_name": "Juniperus procumbens"},
        ]}
    )
    server.expect_request("/search").respond_with_json(
        {
            "answer": (
                "Ficus retusa es una especie tropical de bonsái muy popular. "
                "Riego: abundante en verano, moderado en invierno; evitar encharcamiento. "
                "Luz: pleno sol o semisombra, mínimo 4 horas de luz directa al día. "
                "Suelo: mezcla drenante de akadama y volcánica en proporción 60/40. "
                "Poda: formación en primavera y verano; pinzado continuo durante el crecimiento. "
                "Plagas habituales: cochinilla, araña roja y pulgones; tratar con aceite de neem. "
                "Cuidados por estación: en primavera fertilizar cada 15 días; en verano riego diario; "
                "en otoño reducir fertilización; en invierno proteger de heladas."
            ),
            "results": [],
        }
    )
    yield server
    server.stop()



