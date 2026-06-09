import json
from datetime import date, timedelta
from typing import AsyncIterator, Callable

from bonsai_sensei.domain.services.mimamori.context import build_work_summaries
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def run_mimamori(
    run_mimamori_reflection: Callable,
    build_bonsai_snapshots_func: Callable,
    build_reflection_context_func: Callable,
    list_all_user_settings_func: Callable,
    list_bonsai_func: Callable,
    list_species_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    send_telegram_message_func: Callable,
    search_memory_func: Callable | None = None,
) -> AsyncIterator[str]:
    today = date.today()
    species_map = {species.id: species.name for species in list_species_func()}
    bonsais = list_bonsai_func()
    bonsai_map = {bonsai.id: bonsai.name for bonsai in bonsais}

    bonsai_snapshots = build_bonsai_snapshots_func(bonsais, species_map)
    overdue_works = list_planned_works_in_date_range_func(
        start_date=date(2000, 1, 1),
        end_date=today - timedelta(days=1),
    )
    upcoming_works = list_planned_works_in_date_range_func(
        start_date=today,
        end_date=today + timedelta(days=14),
    )
    overdue_summaries = build_work_summaries(overdue_works, bonsai_map)
    upcoming_summaries = build_work_summaries(upcoming_works, bonsai_map)

    for user_settings in list_all_user_settings_func():
        if not user_settings.telegram_chat_id:
            continue

        logger.info("Running mimamori for user_id=%s", user_settings.user_id)

        recent_memory_facts = None
        if search_memory_func:
            recent_memory_facts = await search_memory_func(
                user_settings.user_id,
                "conversaciones recientes bonsáis últimos 7 días",
            )

        context = await build_reflection_context_func(
            today=today,
            bonsai_snapshots=bonsai_snapshots,
            overdue_summaries=overdue_summaries,
            upcoming_summaries=upcoming_summaries,
            user_settings=user_settings,
            recent_memory_facts=recent_memory_facts,
        )

        response_text = await run_mimamori_reflection(context, user_id=user_settings.user_id)
        await send_telegram_message_func(user_settings.telegram_chat_id, response_text)

        yield json.dumps({
            "user_id": user_settings.user_id,
            "date": today.isoformat(),
            "bonsai_count": len(bonsais),
            "response": response_text,
        })
