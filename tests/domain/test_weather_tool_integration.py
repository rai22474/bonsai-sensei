import logging
import pytest
from bonsai_sensei.domain.weather_tool import get_weather


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_weather_integration_real_call():
    """
    Integration test that actually calls the wttr.in API.
    This test verifies that the external service is reachable and returning expected format.
    """
    location = "Madrid"
    result = await get_weather(location)
    
    logging.info(f"Integration test result: {result}")
    
    assert result.startswith(f"Weather in {location}:")
    assert "°C" in result or "°F" in result
