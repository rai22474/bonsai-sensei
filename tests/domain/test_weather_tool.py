import pytest
import pytest_asyncio
import respx
from httpx import Response
from bonsai_sensei.domain.weather_tool import get_weather


@pytest.mark.asyncio
async def should_call_weather_api(weather_success_result):
    assert weather_success_result["route_called"] is True


@pytest.mark.asyncio
async def should_include_weather_header(weather_success_result):
    location = weather_success_result["location"]
    assert weather_success_result["result"].startswith(f"Weather in {location}:")


@pytest.mark.asyncio
async def should_include_current_condition(weather_success_result):
    assert "Current: Partly cloudy, 15°C" in weather_success_result["result"]


@pytest.mark.asyncio
async def should_include_min_max(weather_success_result):
    assert "Min/Max: 10°C/20°C" in weather_success_result["result"]


@pytest.mark.asyncio
async def should_include_frost_chance(weather_success_result):
    assert "Max Frost Chance: 50%" in weather_success_result["result"]


@pytest.mark.asyncio
async def should_include_midnight_forecast(weather_success_result):
    assert "00:00h: 10°C" in weather_success_result["result"]


@pytest.mark.asyncio
async def should_include_noon_forecast(weather_success_result):
    assert "12:00h: 18°C, Frost chance: 50%" in weather_success_result["result"]


@pytest.mark.asyncio
async def should_return_message_when_location_missing():
    result = await get_weather("")
    assert result == "Please provide a location."


@pytest.mark.asyncio
async def should_call_weather_api_on_error(weather_api_error_result):
    assert weather_api_error_result["route_called"] is True


@pytest.mark.asyncio
async def should_return_message_on_api_error(weather_api_error_result):
    location = weather_api_error_result["location"]
    assert weather_api_error_result["result"] == f"Could not fetch weather for {location}."


@pytest.mark.asyncio
async def should_call_weather_api_on_network_error(weather_network_error_result):
    assert weather_network_error_result["route_called"] is True


@pytest.mark.asyncio
async def should_return_error_message_on_network_error(weather_network_error_result):
    assert "Error retrieving weather information" in weather_network_error_result["result"]


@pytest.mark.asyncio
async def should_return_exception_details_on_network_error(weather_network_error_result):
    assert "Network error" in weather_network_error_result["result"]


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

    return {"location": location, "result": result, "route_called": route_called}


@pytest_asyncio.fixture
async def weather_network_error_result():
    location = "ErrorCity"
    async with respx.mock:
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            side_effect=Exception("Network error")
        )
        result = await get_weather(location)
        route_called = route.called

    return {"result": result, "route_called": route_called}
