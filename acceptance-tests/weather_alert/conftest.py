import re

import pytest
from pytest_httpserver import HTTPServer

from http_client import delete, put, reset_session

STUB_PORT = 8070
TEST_USER_ID = "weather-alert-test-user"

FROST_WEATHER_PAYLOAD = {
    "current_condition": [{"temp_C": "-2", "weatherDesc": [{"value": "Clear"}]}],
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

SAFE_WEATHER_PAYLOAD = {
    "current_condition": [{"temp_C": "18", "weatherDesc": [{"value": "Sunny"}]}],
    "weather": [
        {
            "mintempC": "12",
            "maxtempC": "25",
            "hourly": [
                {"time": "0600", "tempC": "12", "chanceoffrost": "0"},
                {"time": "1200", "tempC": "22", "chanceoffrost": "0"},
                {"time": "1800", "tempC": "18", "chanceoffrost": "0"},
            ],
        }
    ],
}


@pytest.fixture
def context():
    return {}


@pytest.fixture(autouse=True)
def cleanup_user_settings():
    yield
    reset_session(TEST_USER_ID)
    delete(f"/api/users/{TEST_USER_ID}/settings")


@pytest.fixture
def frost_weather_server():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/.+"), query_string="format=j1").respond_with_json(
        FROST_WEATHER_PAYLOAD
    )
    yield server
    server.stop()


@pytest.fixture
def safe_weather_server():
    server = HTTPServer(host="0.0.0.0", port=STUB_PORT)
    server.start()
    server.expect_request(re.compile(r"/.+"), query_string="format=j1").respond_with_json(
        SAFE_WEATHER_PAYLOAD
    )
    yield server
    server.stop()
