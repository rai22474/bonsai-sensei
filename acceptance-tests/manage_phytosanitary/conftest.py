import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, parsers

from http_client import delete, post
from manage_phytosanitary.phytosanitary_api import create_phytosanitary, delete_phytosanitary_by_name

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
        {"answer": "Ficha de uso disponible.", "results": []}
    )
    yield server
    server.stop()


@given(parsers.parse('phytosanitary product "{name}" exists'))
def ensure_phytosanitary_exists(context, name):
    create_phytosanitary(post, name, "Ficha de uso disponible.", "2 ml por litro de agua.", "Hongos y plagas", [])
    context["phytosanitaries_created"].append(name)
