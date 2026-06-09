from datetime import date
from pathlib import Path
from typing import Callable

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_SEASON_BY_MONTH = {
    1: "invierno", 2: "invierno",
    3: "primavera", 4: "primavera", 5: "primavera",
    6: "verano", 7: "verano", 8: "verano",
    9: "otoño", 10: "otoño", 11: "otoño",
    12: "invierno",
}
_SPANISH_DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
_template = _env.get_template("reflection_context.j2")


def build_bonsai_snapshots(
    bonsais,
    species_map: dict,
    list_bonsai_events_func: Callable,
    get_active_development_plan_func: Callable,
    get_active_fertilization_plan_func: Callable,
    get_recent_unlinked_pest_events_func: Callable,
    get_recently_abandoned_fertilization_plans_func: Callable,
    get_recently_abandoned_development_plans_func: Callable,
) -> list[dict]:
    snapshots = []
    for bonsai in bonsais:
        events = list_bonsai_events_func(bonsai_id=bonsai.id)
        last_event = events[-1] if events else None
        dev_plan = get_active_development_plan_func(bonsai_id=bonsai.id)
        fert_plan = get_active_fertilization_plan_func(bonsai_id=bonsai.id)
        fertilization_outdated = (
            dev_plan is not None
            and fert_plan is not None
            and dev_plan.created_at > fert_plan.created_at
        )
        unlinked_pests = get_recent_unlinked_pest_events_func(bonsai_id=bonsai.id, hours=720)
        abandoned_fert = get_recently_abandoned_fertilization_plans_func(bonsai_id=bonsai.id)
        abandoned_dev = get_recently_abandoned_development_plans_func(bonsai_id=bonsai.id)
        plans_pending_recreation = (
            (["fertilization"] if abandoned_fert else [])
            + (["design"] if abandoned_dev else [])
        )
        snapshots.append({
            "name": bonsai.name,
            "species_name": species_map.get(bonsai.species_id, "Especie desconocida"),
            "development_phase": dev_plan.current_phase if dev_plan else None,
            "design_goal": dev_plan.design_goal if dev_plan else None,
            "last_event_type": last_event["event_type"] if last_event else None,
            "last_event_date": last_event["occurred_at"][:10] if last_event else None,
            "fertilization_outdated": fertilization_outdated,
            "fertilization_plan_goal": fert_plan.goal if fert_plan and fertilization_outdated else None,
            "current_design_goal": dev_plan.design_goal if dev_plan and fertilization_outdated else None,
            "unlinked_pest_names": [event.payload.get("pest_name") for event in unlinked_pests],
            "fertilization_at_risk": bool(unlinked_pests) and fert_plan is not None,
            "design_at_risk": bool(unlinked_pests) and dev_plan is not None,
            "plans_pending_recreation": plans_pending_recreation,
        })
    return snapshots


def build_work_summaries(planned_works, bonsai_map: dict) -> list[dict]:
    return [
        {
            "bonsai_name": bonsai_map.get(work.bonsai_id, f"Bonsái {work.bonsai_id}"),
            "work_type": work.work_type,
            "scheduled_date": work.scheduled_date.isoformat(),
        }
        for work in planned_works
    ]


async def build_reflection_context(
    today: date,
    bonsai_snapshots: list[dict],
    overdue_summaries: list[dict],
    upcoming_summaries: list[dict],
    user_settings,
    fetch_weather_func: Callable,
    recent_memory_facts: str | None = None,
) -> str:
    weather_summary = None
    if user_settings.location:
        weather_result = await fetch_weather_func(user_settings.location)
        if weather_result.get("status") == "success":
            weather_summary = weather_result["result"]["summary"]
    return _template.render(
        current_date=today.isoformat(),
        day_of_week=_SPANISH_DAY_NAMES[today.weekday()],
        season=_SEASON_BY_MONTH[today.month],
        is_friday=today.weekday() == 4,
        bonsais=bonsai_snapshots,
        overdue_works=overdue_summaries,
        upcoming_works=upcoming_summaries,
        weather=weather_summary,
        location=user_settings.location,
        recent_memory_facts=recent_memory_facts,
    )
