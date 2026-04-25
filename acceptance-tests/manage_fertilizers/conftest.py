import re
import uuid

import pytest
from pytest_httpserver import HTTPServer
from pytest_bdd import given, then, parsers

from http_client import delete, get, post
from manage_fertilizers.fertilizer_api import create_fertilizer, delete_fertilizer_by_name, find_fertilizer_by_name

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
            "answer": (
                "BioGrow es un fertilizante orgánico líquido para bonsáis. "
                "Composición NPK: 5-3-5 con micronutrientes (Fe, Mn, Zn). "
                "Dosis recomendada: 2 ml por litro de agua. "
                "Época de aplicación: primavera y verano durante el período de crecimiento activo. "
                "Modo de aplicación: diluir en agua de riego, aplicar cada dos semanas. "
                "Precauciones: no aplicar en días de calor extremo ni en plantas recién trasplantadas."
            ),
            "results": [],
        }
    )
    yield server
    server.stop()


@given(parsers.parse('fertilizer "{name}" exists'))
def ensure_fertilizer_exists(context, name):
    create_fertilizer(post, name)
    context["fertilizers_created"].append(name)


@then(parsers.parse('fertilizer "{name}" should have a wiki page'))
def assert_fertilizer_has_wiki_page(name):
    fertilizer = find_fertilizer_by_name(get, name)
    wiki_path = (fertilizer or {}).get("wiki_path")
    assert wiki_path, f"Expected fertilizer '{name}' to have a wiki_path, got: {fertilizer}"
    content = get(f"/api/wiki?path={wiki_path}").get("content", "")
    assert content, f"Expected wiki page at '{wiki_path}' to have content, got empty."
