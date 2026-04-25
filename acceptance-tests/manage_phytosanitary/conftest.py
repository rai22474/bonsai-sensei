import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, then, parsers

from http_client import delete, get, post
from manage_phytosanitary.phytosanitary_api import create_phytosanitary, delete_phytosanitary_by_name, find_phytosanitary_by_name

STUB_PORT = 8070


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-phytosanitary-{uuid.uuid4().hex}",
        "phytosanitaries_created": [],
    }


@pytest.fixture(autouse=True)
def cleanup_phytosanitaries(context):
    yield
    for name in context["phytosanitaries_created"]:
        delete_phytosanitary_by_name(delete, name)


@pytest.fixture
def external_stubs():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/search.*")).respond_with_json(
        {
            "answer": (
                "Neem Oil es un insecticida y fungicida orgánico de origen natural. "
                "Principio activo: azadirachtina al 0.3%. "
                "Dosis recomendada: 2 ml por litro de agua con unas gotas de jabón neutro como emulsionante. "
                "Aplicación: pulverizar por el envés de las hojas, evitar horas de sol directo. "
                "Plagas y enfermedades objetivo: araña roja, cochinilla, pulgones, oídio y mildiu. "
                "Precauciones: no aplicar en temperaturas superiores a 30°C, tóxico para abejas en aplicación directa."
            ),
            "results": [],
        }
    )
    yield server
    server.stop()


@given(parsers.parse('phytosanitary product "{name}" exists'))
def ensure_phytosanitary_exists(context, name):
    create_phytosanitary(post, name)
    context["phytosanitaries_created"].append(name)


@then(parsers.parse('phytosanitary product "{name}" should have a wiki page'))
def assert_phytosanitary_has_wiki_page(name):
    phytosanitary = find_phytosanitary_by_name(get, name)
    wiki_path = (phytosanitary or {}).get("wiki_path")
    assert wiki_path, f"Expected phytosanitary '{name}' to have a wiki_path, got: {phytosanitary}"
    content = get(f"/api/wiki?path={wiki_path}").get("content", "")
    assert content, f"Expected wiki page at '{wiki_path}' to have content, got empty."
