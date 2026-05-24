import logging
import os
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger


async def _run_wiki_dreamer(run_wiki_dreamer: Callable) -> None:
    logging.info("Running scheduled wiki dreamer")
    await run_wiki_dreamer()


def create_wiki_dreamer_scheduler(run_wiki_dreamer: Callable) -> AsyncIOScheduler:
    """Create and start an APScheduler that runs the wiki dreamer at a configurable interval.

    The interval is read from WIKI_DREAMER_INTERVAL_SECONDS (default 1800 = 30 minutes).
    The scheduler must be shut down by the caller.
    """
    interval_seconds = int(os.getenv("WIKI_DREAMER_INTERVAL_SECONDS", str(30 * 60)))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_wiki_dreamer,
        trigger=IntervalTrigger(seconds=interval_seconds),
        kwargs={"run_wiki_dreamer": run_wiki_dreamer},
    )
    scheduler.start()
    return scheduler
