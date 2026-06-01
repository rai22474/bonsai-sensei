import logging
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bonsai_sensei.domain.services.cultivation.plan.weekend_plan_runner import run_weekend_plan_reminders


async def _dispatch_weekend_plan_reminders(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    list_bonsai_func: Callable,
    send_telegram_message_func: Callable,
):
    logging.info("Running scheduled weekend plan reminders")
    async for _ in run_weekend_plan_reminders(
        advisor=advisor,
        list_all_user_settings_func=list_all_user_settings_func,
        list_planned_works_in_date_range_func=list_planned_works_in_date_range_func,
        list_bonsai_func=list_bonsai_func,
        send_telegram_message_func=send_telegram_message_func,
    ):
        pass


def create_weekend_plan_scheduler(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    list_bonsai_func: Callable,
    send_telegram_message_func: Callable,
) -> AsyncIOScheduler:
    """Create and start an APScheduler that sends weekend plan reminders every Friday at 17:00."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _dispatch_weekend_plan_reminders,
        trigger=CronTrigger(day_of_week="fri", hour=17, minute=0),
        kwargs={
            "advisor": advisor,
            "list_all_user_settings_func": list_all_user_settings_func,
            "list_planned_works_in_date_range_func": list_planned_works_in_date_range_func,
            "list_bonsai_func": list_bonsai_func,
            "send_telegram_message_func": send_telegram_message_func,
        },
    )
    scheduler.start()
    return scheduler
