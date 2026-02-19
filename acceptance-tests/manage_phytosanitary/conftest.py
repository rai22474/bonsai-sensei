import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, parsers

from http_client import advise

STUB_PORT = 8070


@pytest.fixture
def context():
    return {"user_id": f"bdd-phytosanitary-{uuid.uuid4().hex}"}


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
def ensure_phytosanitary_exists(context, name, external_stubs):
    advise(
        text=f"Da de alta el fitosanitario {name}.",
        user_id=context["user_id"],
    )
    advise(
        text="Aceptar",
        user_id=context["user_id"],
    )
