from datetime import date
from types import SimpleNamespace

import pytest
from hamcrest import assert_that, contains_string, not_

from bonsai_sensei.domain.services.mimamori.context import build_reflection_context


@pytest.mark.asyncio
async def should_include_bonsai_name_in_rendered_context():
    bonsai_snapshots = [_make_snapshot("Hanako")]
    result = await build_reflection_context(
        today=date(2026, 6, 9),
        bonsai_snapshots=bonsai_snapshots,
        overdue_summaries=[],
        upcoming_summaries=[],
        user_settings=_make_user_settings(location=None),
        fetch_weather_func=_no_weather,
    )
    assert_that(result, contains_string("Hanako"))


@pytest.mark.asyncio
async def should_include_season_in_rendered_context():
    result = await build_reflection_context(
        today=date(2026, 6, 9),
        bonsai_snapshots=[],
        overdue_summaries=[],
        upcoming_summaries=[],
        user_settings=_make_user_settings(location=None),
        fetch_weather_func=_no_weather,
    )
    assert_that(result, contains_string("verano"))


@pytest.mark.asyncio
async def should_not_call_weather_when_no_location():
    called = {"count": 0}

    async def spy_weather(location):
        called["count"] += 1
        return {"status": "success", "result": {"summary": "sunny"}}

    await build_reflection_context(
        today=date(2026, 6, 9),
        bonsai_snapshots=[],
        overdue_summaries=[],
        upcoming_summaries=[],
        user_settings=_make_user_settings(location=None),
        fetch_weather_func=spy_weather,
    )
    assert_that(called["count"], equal_to(0))


@pytest.mark.asyncio
async def should_include_weather_when_location_set_and_fetch_succeeds():
    async def sunny_weather(location):
        return {"status": "success", "result": {"summary": "Soleado, 28°C"}}

    result = await build_reflection_context(
        today=date(2026, 6, 9),
        bonsai_snapshots=[],
        overdue_summaries=[],
        upcoming_summaries=[],
        user_settings=_make_user_settings(location="Madrid"),
        fetch_weather_func=sunny_weather,
    )
    assert_that(result, contains_string("Soleado, 28°C"))


@pytest.mark.asyncio
async def should_omit_weather_when_fetch_fails():
    async def failing_weather(location):
        return {"status": "error"}

    result = await build_reflection_context(
        today=date(2026, 6, 9),
        bonsai_snapshots=[],
        overdue_summaries=[],
        upcoming_summaries=[],
        user_settings=_make_user_settings(location="Madrid"),
        fetch_weather_func=failing_weather,
    )
    assert_that(result, not_(contains_string("Tiempo en")))


@pytest.mark.asyncio
async def should_include_overdue_work_in_context():
    overdue = [{"bonsai_name": "Hanako", "work_type": "fertilizer_application", "scheduled_date": "2026-05-01"}]
    result = await build_reflection_context(
        today=date(2026, 6, 9),
        bonsai_snapshots=[],
        overdue_summaries=overdue,
        upcoming_summaries=[],
        user_settings=_make_user_settings(location=None),
        fetch_weather_func=_no_weather,
    )
    assert_that(result, contains_string("Trabajos vencidos"))


def _make_snapshot(name: str) -> dict:
    return {
        "name": name,
        "species_name": "Ficus retusa",
        "development_phase": None,
        "design_goal": None,
        "last_event_type": None,
        "last_event_date": None,
        "fertilization_outdated": False,
        "fertilization_plan_goal": None,
        "current_design_goal": None,
    }


def _make_user_settings(location):
    return SimpleNamespace(location=location)


async def _no_weather(location):
    return {"status": "error"}


def equal_to(value):
    from hamcrest import equal_to as _equal_to
    return _equal_to(value)
