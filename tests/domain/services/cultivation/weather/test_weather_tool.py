import httpx
import pytest
import pytest_asyncio
import respx
from httpx import Response
from hamcrest import assert_that, contains_string, equal_to, starts_with
from bonsai_sensei.domain.services.cultivation.weather.weather_tool import get_weather


@pytest.mark.asyncio
async def should_call_weather_api(weather_success_result):
    assert_that(weather_success_result["route_called"], equal_to(True))


@pytest.mark.asyncio
async def should_include_weather_header(weather_success_result):
    location = weather_success_result["location"]
    assert_that(
        weather_success_result["result"]["result"]["summary"],
        starts_with(f"Weather in {location}:"),
    )


@pytest.mark.asyncio
async def should_include_current_condition(weather_success_result):
    assert_that(
        weather_success_result["result"]["result"]["summary"],
        contains_string("Current: Partly cloudy, 15°C"),
    )


@pytest.mark.asyncio
async def should_include_min_max(weather_success_result):
    assert_that(
        weather_success_result["result"]["result"]["summary"],
        contains_string("Min/Max: 10°C/20°C"),
    )


@pytest.mark.asyncio
async def should_include_frost_chance(weather_success_result):
    assert_that(
        weather_success_result["result"]["result"]["summary"],
        contains_string("Max Frost Chance: 50%"),
    )


@pytest.mark.asyncio
async def should_include_midnight_forecast(weather_success_result):
    assert_that(
        weather_success_result["result"]["result"]["summary"],
        contains_string("00:00h: 10°C"),
    )


@pytest.mark.asyncio
async def should_include_noon_forecast(weather_success_result):
    assert_that(
        weather_success_result["result"]["result"]["summary"],
        contains_string("12:00h: 18°C, Frost chance: 50%"),
    )


@pytest.mark.asyncio
async def should_return_message_when_location_missing():
    result = await get_weather("")
    assert_that(result, equal_to({"status": "error", "message": "Please provide a location."}))


@pytest.mark.asyncio
async def should_call_weather_api_on_error(weather_api_error_result):
    assert_that(weather_api_error_result["route_called"], equal_to(True))


@pytest.mark.asyncio
async def should_return_message_on_api_error(weather_api_error_result):
    location = weather_api_error_result["location"]
    assert_that(
        weather_api_error_result["result"],
        equal_to(f"Could not fetch weather for {location}."),
    )


@pytest.mark.asyncio
async def should_call_weather_api_on_network_error(weather_network_error_result):
    assert_that(weather_network_error_result["route_called"], equal_to(True))


@pytest.mark.asyncio
async def should_return_error_message_on_network_error(weather_network_error_result):
    assert_that(
        weather_network_error_result["result"],
        contains_string("Error retrieving weather information"),
    )


@pytest.mark.asyncio
async def should_return_exception_details_on_network_error(weather_network_error_result):
    assert_that(
        weather_network_error_result["result"],
        contains_string("Network error"),
    )


@pytest_asyncio.fixture
async def weather_success_result():
    location = "Madrid"
    mock_response = {
        "current_condition": [
            {"temp_C": "15", "weatherDesc": [{"value": "Partly cloudy"}]}
        ],
        "weather": [
            {
                "mintempC": "10",
                "maxtempC": "20",
                "hourly": [
                    {"time": "0", "tempC": "10", "chanceoffrost": "0"},
                    {"time": "1200", "tempC": "18", "chanceoffrost": "50"},
                ],
            }
        ],
    }

    async with respx.mock:
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            return_value=Response(200, json=mock_response)
        )
        result = await get_weather(location)
        route_called = route.called

    return {"location": location, "result": result, "route_called": route_called}


@pytest_asyncio.fixture
async def weather_api_error_result():
    location = "UnknownCity"
    async with respx.mock:
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            return_value=Response(404)
        )
        result = await get_weather(location)
        route_called = route.called

    return {
        "location": location,
        "result": result.get("message"),
        "route_called": route_called,
    }


@pytest_asyncio.fixture
async def weather_network_error_result():
    location = "ErrorCity"
    async with respx.mock:
        request = httpx.Request("GET", f"https://wttr.in/{location}?format=j1")
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            side_effect=httpx.RequestError("Network error", request=request)
        )
        result = await get_weather(location)
        route_called = route.called

    return {
        "result": result.get("message"),
        "route_called": route_called,
    }
