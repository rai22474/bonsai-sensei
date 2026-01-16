import pytest
import respx
from httpx import Response
from bonsai_sensei.domain.weather_tool import get_weather
import json


@pytest.mark.asyncio
async def test_get_weather_success():
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
                    {"time": "1200", "tempC": "18", "chanceoffrost": "50"}
                ]
            }
        ]
    }
    
    async with respx.mock:
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            return_value=Response(200, json=mock_response)
        )
        
        result = await get_weather(location)
        
        assert route.called
        assert result.startswith(f"Weather in {location}:")
        assert "Current: Partly cloudy, 15°C" in result
        assert "Min/Max: 10°C/20°C" in result
        assert "Max Frost Chance: 50%" in result
        assert "00:00h: 10°C" in result
        assert "12:00h: 18°C, Frost chance: 50%" in result


@pytest.mark.asyncio
async def test_get_weather_empty_location():
    result = await get_weather("")
    assert result == "Please provide a location."


@pytest.mark.asyncio
async def test_get_weather_api_error():
    location = "UnknownCity"
    
    async with respx.mock:
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            return_value=Response(404)
        )
        
        result = await get_weather(location)
        
        assert route.called
        assert result == f"Could not fetch weather for {location}."


@pytest.mark.asyncio
async def test_get_weather_network_exception():
    location = "ErrorCity"
    
    async with respx.mock:
        route = respx.get(f"https://wttr.in/{location}?format=j1").mock(
            side_effect=Exception("Network error")
        )
        
        result = await get_weather(location)
        
        assert route.called
        assert "Error retrieving weather information" in result
        assert "Network error" in result
