import logging
import pytest
import pytest_asyncio
from hamcrest import assert_that, any_of, contains_string, starts_with
from bonsai_sensei.domain.services.weather.weather_tool import get_weather


@pytest.mark.asyncio
@pytest.mark.integration
async def should_include_header_in_integration_result(weather_integration_result):
    location = weather_integration_result["location"]
    assert_that(
        weather_integration_result["result"],
        starts_with(f"Weather in {location}:"),
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def should_include_temperature_unit_in_integration_result(weather_integration_result):
    result = weather_integration_result["result"]
    assert_that(result, any_of(contains_string("°C"), contains_string("°F")))


@pytest_asyncio.fixture(scope="module")
async def weather_integration_result():
    location = "Madrid"
    result = await get_weather(location)
    logging.info(f"Integration test result: {result}")
    return {"location": location, "result": result}
