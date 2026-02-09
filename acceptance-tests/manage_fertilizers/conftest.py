import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, parsers

from http_client import advise

STUB_PORT = 8070


@pytest.fixture
def context():
    return {"user_id": f"bdd-fertilizer-{uuid.uuid4().hex}"}


@pytest.fixture
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


@given(parsers.parse('fertilizer "{name}" exists'))
def ensure_fertilizer_exists(context, name, external_stubs):
    advise(
        text=f"Da de alta el fertilizante {name}.",
        user_id=context["user_id"],
    )
    advise(
        text=f"Sí, confirma el alta del fertilizante {name}.",
        user_id=context["user_id"],
    )
