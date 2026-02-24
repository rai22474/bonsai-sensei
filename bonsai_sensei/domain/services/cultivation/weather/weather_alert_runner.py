import json
from typing import AsyncIterator, Callable

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

WEATHER_ALERT_PROMPT = (
    "Comprueba el tiempo para la ubicación {location} y evalúa si hay algún riesgo "
    "para mis bonsáis hoy. Sé conciso."
)


async def run_weather_alerts(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    send_telegram_message_func: Callable,
) -> AsyncIterator[str]:
    """Evaluate weather risks for all registered users via the sensei advisor.

    For each user with a registered location, the sensei agent fetches the weather
    and evaluates potential risks for the bonsai collection. Results are yielded
    as JSON strings for SSE streaming, and sent via Telegram when configured.

    Args:
        advisor: The sensei advisor callable (async).
        list_all_user_settings_func: Returns all UserSettings records.
        send_telegram_message_func: Sends a Telegram message to a chat_id (async).

    Yields:
        JSON-serialized dicts with user_id, location, and the sensei's response text.
    """
    all_user_settings = list_all_user_settings_func()
    for user_settings in all_user_settings:
        if not user_settings.location:
            continue

        logger.info(
            "Running weather alert for user_id=%s location=%s",
            user_settings.user_id,
            user_settings.location,
        )

        prompt = WEATHER_ALERT_PROMPT.format(location=user_settings.location)
        response = await advisor(prompt, user_id=user_settings.user_id)

        if user_settings.telegram_chat_id:
            await send_telegram_message_func(user_settings.telegram_chat_id, response.text)

        yield json.dumps({
            "user_id": user_settings.user_id,
            "location": user_settings.location,
            "response": response.text,
        })
