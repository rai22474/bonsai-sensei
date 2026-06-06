import json
from datetime import date, timedelta
from pathlib import Path
from typing import AsyncIterator, Callable

from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_SEASON_BY_MONTH = {
    1: "invierno", 2: "invierno",
    3: "primavera", 4: "primavera", 5: "primavera",
    6: "verano", 7: "verano", 8: "verano",
    9: "otoño", 10: "otoño", 11: "otoño",
    12: "invierno",
}
_SPANISH_DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


async def run_mimamori(
    advisor: Callable,
    list_all_user_settings_func: Callable,
    list_bonsai_func: Callable,
    list_species_func: Callable,
    list_bonsai_events_func: Callable,
    get_active_development_plan_func: Callable,
    list_planned_works_in_date_range_func: Callable,
    fetch_weather_func: Callable,
    send_telegram_message_func: Callable,
) -> AsyncIterator[str]:
    today = date.today()
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("reflection_prompt.j2")

    species_map = {species.id: species.name for species in list_species_func()}
    bonsais = list_bonsai_func()
    bonsai_map = {bonsai.id: bonsai.name for bonsai in bonsais}
    bonsai_snapshots = _build_bonsai_snapshots(bonsais, species_map, list_bonsai_events_func, get_active_development_plan_func)

    overdue_works = list_planned_works_in_date_range_func(
        start_date=date(2000, 1, 1),
        end_date=today - timedelta(days=1),
    )
    upcoming_works = list_planned_works_in_date_range_func(
        start_date=today,
        end_date=today + timedelta(days=14),
    )

    overdue_summaries = _build_work_summaries(overdue_works, bonsai_map)
    upcoming_summaries = _build_work_summaries(upcoming_works, bonsai_map)

    for user_settings in list_all_user_settings_func():
        if not user_settings.telegram_chat_id:
            continue

        logger.info("Running mimamori for user_id=%s", user_settings.user_id)

        weather_summary = None
        if user_settings.location:
            weather_result = await fetch_weather_func(user_settings.location)
            if weather_result.get("status") == "success":
                weather_summary = weather_result["result"]["summary"]

        prompt = template.render(
            current_date=today.isoformat(),
            day_of_week=_SPANISH_DAY_NAMES[today.weekday()],
            season=_SEASON_BY_MONTH[today.month],
            is_friday=today.weekday() == 4,
            bonsais=bonsai_snapshots,
            overdue_works=overdue_summaries,
            upcoming_works=upcoming_summaries,
            weather=weather_summary,
            location=user_settings.location,
        )

        response = await advisor(prompt, user_id=user_settings.user_id)
        await send_telegram_message_func(user_settings.telegram_chat_id, response.text)

        yield json.dumps({
            "user_id": user_settings.user_id,
            "date": today.isoformat(),
            "bonsai_count": len(bonsais),
            "response": response.text,
        })


def _build_bonsai_snapshots(
    bonsais,
    species_map: dict,
    list_bonsai_events_func: Callable,
    get_active_development_plan_func: Callable,
) -> list[dict]:
    snapshots = []
    for bonsai in bonsais:
        events = list_bonsai_events_func(bonsai_id=bonsai.id)
        last_event = events[-1] if events else None
        dev_plan = get_active_development_plan_func(bonsai_id=bonsai.id)
        snapshots.append({
            "name": bonsai.name,
            "species_name": species_map.get(bonsai.species_id, "Especie desconocida"),
            "development_phase": dev_plan.current_phase if dev_plan else None,
            "design_goal": dev_plan.design_goal if dev_plan else None,
            "last_event_type": last_event["event_type"] if last_event else None,
            "last_event_date": last_event["occurred_at"][:10] if last_event else None,
        })
    return snapshots


def _build_work_summaries(planned_works, bonsai_map: dict) -> list[dict]:
    return [
        {
            "bonsai_name": bonsai_map.get(work.bonsai_id, f"Bonsái {work.bonsai_id}"),
            "work_type": work.work_type,
            "scheduled_date": work.scheduled_date.isoformat(),
        }
        for work in planned_works
    ]
