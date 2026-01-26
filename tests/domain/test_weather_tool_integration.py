import logging
import pytest
import pytest_asyncio
from bonsai_sensei.domain.weather_tool import get_weather


@pytest.mark.asyncio
@pytest.mark.integration
async def should_include_header_in_integration_result(weather_integration_result):
    location = weather_integration_result["location"]
    assert weather_integration_result["result"].startswith(f"Weather in {location}:")


@pytest.mark.asyncio
@pytest.mark.integration
async def should_include_temperature_unit_in_integration_result(weather_integration_result):
    result = weather_integration_result["result"]
    assert "°C" in result or "°F" in result


@pytest_asyncio.fixture(scope="module")
async def weather_integration_result():
    location = "Madrid"
    result = await get_weather(location)
    logging.info(f"Integration test result: {result}")
    return {"location": location, "result": result}
