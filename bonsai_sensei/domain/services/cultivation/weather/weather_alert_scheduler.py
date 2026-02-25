import logging
import os
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bonsai_sensei.domain.services.cultivation.weather.weather_alert_runner import run_weather_alerts


async def _dispatch_weather_alerts(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    send_telegram_message_func: Callable,
):
    logging.info("Running scheduled weather alerts")
    async for _ in run_weather_alerts(
        advisor=advisor,
        list_all_user_settings_func=list_all_user_settings_func,
        send_telegram_message_func=send_telegram_message_func,
    ):
        pass


def create_weather_alert_scheduler(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    send_telegram_message_func: Callable,
) -> AsyncIOScheduler:
    """Create and start an APScheduler that dispatches weather alerts at a configurable interval.

    The interval is read from the WEATHER_ALERT_INTERVAL_SECONDS environment variable
    (defaults to 900 seconds / 15 minutes). The scheduler must be shut down by the caller.
    """
    interval_seconds = int(os.getenv("WEATHER_ALERT_INTERVAL_SECONDS", str(15 * 60)))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _dispatch_weather_alerts,
        trigger=IntervalTrigger(seconds=interval_seconds),
        kwargs={
            "advisor": advisor,
            "list_all_user_settings_func": list_all_user_settings_func,
            "send_telegram_message_func": send_telegram_message_func,
        },
    )
    scheduler.start()
    return scheduler
