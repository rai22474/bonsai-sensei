import os
import re

import pytest
from pytest_bdd import given, scenario, then, when, parsers
from pytest_httpserver import HTTPServer
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from http_client import request_json
from judge import create_recommendation_metric
STUB_PORT = int(os.getenv("WEATHER_STUB_PORT", "8070"))


@scenario("features/protect_bonsai.feature", "Advise no protection for mild night")
def test_advise_no_protection_for_mild_night():
    return None


@pytest.fixture
def context():
    return {}


@pytest.fixture
def weather_stub_server():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    payload = {
        "current_condition": [{"temp_C": "8", "weatherDesc": [{"value": "Clear"}]}],
        "weather": [
            {
                "mintempC": "6",
                "maxtempC": "12",
                "hourly": [
                    {"time": "0000", "tempC": "7", "chanceoffrost": "0"},
                    {"time": "0300", "tempC": "6", "chanceoffrost": "0"},
                    {"time": "0600", "tempC": "8", "chanceoffrost": "0"},
                ],
            }
        ],
    }
    server.expect_request(re.compile(r"/.+"), query_string="format=j1").respond_with_json(payload)
    server.expect_request("/api/v1/plants/search").respond_with_json(
        {"data": [{"scientific_name": "Juniperus procumbens"}]}
    )
    server.expect_request("/search").respond_with_json(
        {"answer": "Guía de cuidado disponible.", "results": []}
    )
    yield server
    server.stop()


@given("a bonsai collection with frost-sensitive bonsais", target_fixture="bonsai_fixture")
def bonsai_fixture(weather_stub_server):
    species = request_json(
        "POST",
        "/api/species",
        {
            "name": "Juniperus procumbens",
            "scientific_name": "Juniperus procumbens",
            "care_guide": {
                "summary": "Tolera frío moderado, pero necesita protección con heladas.",
                "temperature_range_celsius": {"min": -2, "max": 25},
            },
        },
    )
    species_id = species.get("id")
    request_json(
        "POST",
        "/api/bonsai",
        {"name": "Sasuke", "species_id": species_id},
    )
    yield
    bonsai_items = request_json("GET", "/api/bonsai") or []
    for item in bonsai_items:
        request_json("DELETE", f"/api/bonsai/{item['id']}")
    species_items = request_json("GET", "/api/species") or []
    for item in species_items:
        request_json("DELETE", f"/api/species/{item['id']}")


@when(parsers.parse('I ask "{question}"'))
def ask_for_protection(context, bonsai_fixture, question):
    response = request_json(
        "POST",
        "/api/advice",
        {"text": question, "user_id": "bdd"},
    )
    context["prompt"] = question
    context["response"] = response.get("response", "")


@then("I get a protection recommendation")
def verify_recommendation(context, bonsai_fixture):
    test_case = LLMTestCase(
        input=context.get("prompt", ""),
        actual_output=context.get("response", ""),
    )
    metric = create_recommendation_metric(
        name="mild_night_no_protection",
        criteria=(
            "The response should state that protection is not needed for tonight in Madrid "
            "and that the bonsai can remain outside. It must avoid recommending protective measures."
        ),
    )
    assert_test(test_case=test_case, metrics=[metric], run_async=False)
