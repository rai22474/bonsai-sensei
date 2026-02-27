import json
from datetime import date, timedelta
from typing import AsyncIterator, Callable

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

WEEKEND_PLAN_PROMPT = """Es viernes por la tarde. Aquí tienes los trabajos planificados para este fin de semana \
(sábado {saturday} y domingo {sunday}):

{planned_works_summary}

Haz un resumen amigable de lo que hay que hacer durante el fin de semana, indicando el bonsái, \
el tipo de trabajo y la fecha. Ten en cuenta que los fines de semana son cuando más tiempo se tiene \
para cuidar los bonsáis."""

NO_WORKS_PROMPT = """Es viernes por la tarde. No hay trabajos planificados para este fin de semana \
(sábado {saturday} y domingo {sunday}). Indícaselo al usuario de forma positiva \
y recuérdale que puede planificar trabajos cuando lo necesite."""


def _upcoming_weekend() -> tuple[date, date]:
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday = today + timedelta(days=days_until_saturday)
    return saturday, saturday + timedelta(days=1)


async def run_weekend_plan_reminders(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    list_bonsai_func: Callable,
    send_telegram_message_func: Callable,
) -> AsyncIterator[str]:
    """Send each registered Telegram user a summary of their bonsai work plan for the upcoming weekend.

    Queries all planned works for next Saturday and Sunday, formats them into a prompt,
    and asks the advisor to generate a friendly message for each user with a telegram_chat_id.

    Args:
        advisor: The sensei advisor callable (async).
        list_all_user_settings_func: Returns all UserSettings records.
        list_planned_works_in_date_range_func: Returns PlannedWork records within a date range.
        list_bonsai_func: Returns all Bonsai records.
        send_telegram_message_func: Sends a Telegram message to a chat_id (async).

    Yields:
        JSON-serialized dicts with user_id, saturday, sunday, and the advisor's response text.
    """
    saturday, sunday = _upcoming_weekend()

    planned_works = list_planned_works_in_date_range_func(start_date=saturday, end_date=sunday)
    bonsai_map = {bonsai.id: bonsai.name for bonsai in list_bonsai_func()}

    if planned_works:
        works_lines = [
            f"- {bonsai_map.get(work.bonsai_id, f'Bonsái {work.bonsai_id}')}: "
            f"{work.work_type} el {work.scheduled_date}"
            for work in planned_works
        ]
        prompt = WEEKEND_PLAN_PROMPT.format(
            saturday=saturday.isoformat(),
            sunday=sunday.isoformat(),
            planned_works_summary="\n".join(works_lines),
        )
    else:
        prompt = NO_WORKS_PROMPT.format(
            saturday=saturday.isoformat(),
            sunday=sunday.isoformat(),
        )

    for user_settings in list_all_user_settings_func():
        if not user_settings.telegram_chat_id:
            continue

        logger.info("Running weekend plan reminder for user_id=%s", user_settings.user_id)
        response = await advisor(prompt, user_id=user_settings.user_id)

        await send_telegram_message_func(user_settings.telegram_chat_id, response.text)

        yield json.dumps({
            "user_id": user_settings.user_id,
            "saturday": saturday.isoformat(),
            "sunday": sunday.isoformat(),
            "response": response.text,
        })
