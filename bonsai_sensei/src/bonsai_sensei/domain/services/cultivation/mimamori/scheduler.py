import logging
import os
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bonsai_sensei.domain.services.cultivation.mimamori.runner import run_mimamori


async def _dispatch_mimamori(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    list_bonsai_func: Callable,
    list_species_func: Callable,
    list_bonsai_events_func: Callable,
    get_active_development_plan_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    fetch_weather_func: Callable,
    send_telegram_message_func: Callable,
):
    logging.info("Running scheduled mimamori reflection")
    async for _ in run_mimamori(
        advisor=advisor,
        list_all_user_settings_func=list_all_user_settings_func,
        list_bonsai_func=list_bonsai_func,
        list_species_func=list_species_func,
        list_bonsai_events_func=list_bonsai_events_func,
        get_active_development_plan_func=get_active_development_plan_func,
        list_planned_works_in_date_range_func=list_planned_works_in_date_range_func,
        fetch_weather_func=fetch_weather_func,
        send_telegram_message_func=send_telegram_message_func,
    ):
        pass


def create_mimamori_scheduler(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    list_bonsai_func: Callable,
    list_species_func: Callable,
    list_bonsai_events_func: Callable,
    get_active_development_plan_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    fetch_weather_func: Callable,
    send_telegram_message_func: Callable,
) -> AsyncIOScheduler:
    """Create and start an APScheduler that runs the daily mimamori reflection.

    The trigger hour is read from MIMAMORI_HOUR (default 8) and minute from
    MIMAMORI_MINUTE (default 0). The scheduler must be shut down by the caller.
    """
    hour = int(os.getenv("MIMAMORI_HOUR", "8"))
    minute = int(os.getenv("MIMAMORI_MINUTE", "0"))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _dispatch_mimamori,
        trigger=CronTrigger(hour=hour, minute=minute),
        kwargs={
            "advisor": advisor,
            "list_all_user_settings_func": list_all_user_settings_func,
            "list_bonsai_func": list_bonsai_func,
            "list_species_func": list_species_func,
            "list_bonsai_events_func": list_bonsai_events_func,
            "get_active_development_plan_func": get_active_development_plan_func,
            "list_planned_works_in_date_range_func": list_planned_works_in_date_range_func,
            "fetch_weather_func": fetch_weather_func,
            "send_telegram_message_func": send_telegram_message_func,
        },
    )
    scheduler.start()
    return scheduler
