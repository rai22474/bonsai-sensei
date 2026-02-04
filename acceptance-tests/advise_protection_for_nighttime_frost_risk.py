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
CRITERIA = "The response should recommend protecting the bonsai tonight and explain frost risk."


@scenario("features/protect_bonsai.feature", "Advise protection for nighttime frost risk")
def test_protect_bonsai():
    return None


@pytest.fixture
def context():
    return {}


@pytest.fixture
def weather_stub_server():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    payload = {
        "current_condition": [{"temp_C": "-1", "weatherDesc": [{"value": "Clear"}]}],
        "weather": [
            {
                "mintempC": "-3",
                "maxtempC": "2",
                "hourly": [
                    {"time": "0000", "tempC": "-2", "chanceoffrost": "90"},
                    {"time": "0300", "tempC": "-3", "chanceoffrost": "95"},
                    {"time": "0600", "tempC": "-1", "chanceoffrost": "85"},
                ],
            }
        ],
    }
    server.expect_request(re.compile(r"/.+"), query_string="format=j1").respond_with_json(payload)
    server.expect_request("/api/v1/plants/search").respond_with_json(
        {"data": [{"scientific_name": "Juniperus procumbens"}]}
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
        "protect_bonsai_recommendation",
        CRITERIA,
    )
    assert_test(test_case=test_case, metrics=[metric], run_async=False)
