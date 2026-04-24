import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, parsers

from http_client import delete, post
from manage_fertilizers.fertilizer_api import create_fertilizer, delete_fertilizer_by_name

STUB_PORT = 8070


@pytest.fixture
def context():
    return {
        "user_id": f"bdd-fertilizer-{uuid.uuid4().hex}",
        "fertilizers_created": [],
    }


@pytest.fixture(autouse=True)
def cleanup_fertilizers(context):
    yield
    for name in context["fertilizers_created"]:
        delete_fertilizer_by_name(delete, name)


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
def ensure_fertilizer_exists(context, name):
    create_fertilizer(post, name)
    context["fertilizers_created"].append(name)
