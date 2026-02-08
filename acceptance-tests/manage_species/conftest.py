import re
import uuid

import pytest
from pytest_httpserver import HTTPServer

from http_client import delete, get, post
from manage_species.species_api import delete_species_by_name

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
        {"answer": "Guía de cuidado disponible.", "results": []}
    )
    yield server
    server.stop()



