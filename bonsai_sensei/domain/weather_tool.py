import httpx
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def get_weather(location: str) -> str:
    """
    Fetches the weather forecast for a given location.

    Args:
        location: The city or place to get the weather for.
    """
    logger.info(f"Fetching weather for: {location}")
    if not location:
        return "Please provide a location."

    url = f"https://wttr.in/{location}?format=%C+%t"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                result = response.text.strip()
                logger.info(f"Weather result: {result}")
                return f"Weather in {location}: {result}"
            else:
                return f"Could not fetch weather for {location}."
        except Exception as e:
            logger.error(f"Error calling wttr.in: {e}")
            return f"Error retrieving weather information."
