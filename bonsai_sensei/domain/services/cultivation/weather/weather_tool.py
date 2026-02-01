import httpx
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def get_weather(location: str) -> str:
    """
    Fetches the weather forecast for a given location.

    Args:
        location: The location to get the weather for. Can be a city name (e.g. "Madrid"),
                  coordinates (e.g. "40.4167,-3.70325"), or a postal code.
                  Using coordinates provides a much more precise forecast.
    """
    logger.info(f"Fetching weather for: {location}")
    if not location:
        return "Please provide a location."

    try:
        data = await _fetch_weather_data(location)
        if data:
            result = _format_weather_report(location, data)
            logger.info(f"Weather result: {result}")
            return result
        else:
            return f"Could not fetch weather for {location}."

    except Exception as e:
        logger.exception(f"Error calling wttr.in for location '{location}': {e}")
        return f"Error retrieving weather information: {str(e)}"


async def _fetch_weather_data(location: str) -> dict | None:
    """Makes the HTTP request to the external weather service."""
    url = f"https://wttr.in/{location}?format=j1"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()

    return None


def _extract_hourly_data(weather_today: dict) -> tuple[str, int]:
    """Parses hourly data to extract formatted string and max frost risk."""
    hourly_info = []
    max_frost_chance = 0

    for hour in weather_today["hourly"]:
        time_str = hour["time"].zfill(4)
        formatted_time = f"{time_str[:2]}:{time_str[2:]}"
        temp = hour["tempC"]
        frost_chance = int(hour.get("chanceoffrost", "0"))

        if frost_chance > max_frost_chance:
            max_frost_chance = frost_chance

        frost_str = f", Frost chance: {frost_chance}%" if frost_chance > 0 else ""
        hourly_info.append(f"{formatted_time}h: {temp}°C{frost_str}")

    return "; ".join(hourly_info), max_frost_chance


def _format_weather_report(location: str, data: dict) -> str:
    """Formats the raw JSON data into a human-readable string."""
    current = data["current_condition"][0]
    weather_today = data["weather"][0]

    current_temp = current["temp_C"]
    desc = current["weatherDesc"][0]["value"]
    min_temp = weather_today["mintempC"]
    max_temp = weather_today["maxtempC"]

    hourly_str, max_frost_chance = _extract_hourly_data(weather_today)

    frost_warning = (
        f" WARNING: High risk of frost ({max_frost_chance}%)."
        if max_frost_chance > 50
        else ""
    )

    result = (
        f"Current: {desc}, {current_temp}°C. "
        f"Min/Max: {min_temp}°C/{max_temp}°C. "
        f"Max Frost Chance: {max_frost_chance}%.{frost_warning} "
        f"Hourly: {hourly_str}"
    )
    return f"Weather in {location}: {result}"
