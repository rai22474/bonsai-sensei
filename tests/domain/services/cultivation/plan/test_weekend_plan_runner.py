from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.weekend_plan_runner import (
    WEEKEND_PLAN_PROMPT,
    NO_WORKS_PROMPT,
    run_weekend_plan_reminders,
)
from bonsai_sensei.domain.user_settings import UserSettings


async def _collect(runner_coro):
    results = []
    async for item in runner_coro:
        results.append(item)
    return results


def _make_planned_work(bonsai_id: int, work_type: str = "fertilizer_application") -> PlannedWork:
    saturday = _next_saturday()
    work = PlannedWork(
        bonsai_id=bonsai_id,
        work_type=work_type,
        payload={"fertilizer_name": "Bio", "amount": "5 ml"},
        scheduled_date=saturday,
    )
    work.id = 1
    return work


def _next_saturday() -> date:
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


@pytest.mark.asyncio
async def should_yield_one_event_per_user_with_telegram_chat_id(
    advisor, user_with_telegram, list_bonsai_func, send_telegram_func
):
    results = await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_with_telegram],
            list_planned_works_in_date_range_func=lambda **_: [],
            list_bonsai_func=list_bonsai_func,
            send_telegram_message_func=send_telegram_func,
        )
    )

    assert len(results) == 1, "Expected exactly one event yielded for the user with telegram"


@pytest.mark.asyncio
async def should_skip_users_without_telegram_chat_id(
    advisor, send_telegram_func, list_bonsai_func
):
    user_without_telegram = UserSettings(user_id="u2", telegram_chat_id=None)

    results = await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_without_telegram],
            list_planned_works_in_date_range_func=lambda **_: [],
            list_bonsai_func=list_bonsai_func,
            send_telegram_message_func=send_telegram_func,
        )
    )

    assert len(results) == 0, "Expected no events for a user without telegram_chat_id"


@pytest.mark.asyncio
async def should_send_telegram_message_for_each_user_with_chat_id(
    advisor, user_with_telegram, list_bonsai_func, send_telegram_func
):
    await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_with_telegram],
            list_planned_works_in_date_range_func=lambda **_: [],
            list_bonsai_func=list_bonsai_func,
            send_telegram_message_func=send_telegram_func,
        )
    )

    assert send_telegram_func.call_count == 1, (
        "Expected send_telegram_message_func to be called once"
    )
    assert send_telegram_func.call_args[0][0] == user_with_telegram.telegram_chat_id, (
        "Expected message sent to the correct chat_id"
    )


@pytest.mark.asyncio
async def should_use_no_works_prompt_when_no_planned_works_exist(
    advisor, user_with_telegram, list_bonsai_func, send_telegram_func
):
    await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_with_telegram],
            list_planned_works_in_date_range_func=lambda **_: [],
            list_bonsai_func=list_bonsai_func,
            send_telegram_message_func=send_telegram_func,
        )
    )

    called_prompt = advisor.call_args[0][0]
    saturday = _next_saturday()
    expected_fragment = NO_WORKS_PROMPT.format(
        saturday=saturday.isoformat(),
        sunday=(saturday + timedelta(days=1)).isoformat(),
    )
    assert expected_fragment in called_prompt, (
        f"Expected no-works prompt when no planned works exist, but got: {called_prompt}"
    )


@pytest.mark.asyncio
async def should_use_weekend_plan_prompt_when_planned_works_exist(
    advisor, user_with_telegram, send_telegram_func
):
    bonsai = Bonsai(name="Hanako", species_id=1)
    bonsai.id = 42
    planned_work = _make_planned_work(bonsai_id=42)

    await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_with_telegram],
            list_planned_works_in_date_range_func=lambda **_: [planned_work],
            list_bonsai_func=lambda: [bonsai],
            send_telegram_message_func=send_telegram_func,
        )
    )

    called_prompt = advisor.call_args[0][0]
    assert "Hanako" in called_prompt, (
        f"Expected bonsai name 'Hanako' in prompt when planned works exist, but got: {called_prompt}"
    )


@pytest.mark.asyncio
async def should_include_work_type_in_prompt_when_planned_works_exist(
    advisor, user_with_telegram, send_telegram_func
):
    bonsai = Bonsai(name="Hanako", species_id=1)
    bonsai.id = 42
    planned_work = _make_planned_work(bonsai_id=42, work_type="transplant")

    await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_with_telegram],
            list_planned_works_in_date_range_func=lambda **_: [planned_work],
            list_bonsai_func=lambda: [bonsai],
            send_telegram_message_func=send_telegram_func,
        )
    )

    called_prompt = advisor.call_args[0][0]
    assert "transplant" in called_prompt, (
        f"Expected work_type 'transplant' in prompt, but got: {called_prompt}"
    )


@pytest.mark.asyncio
async def should_include_response_text_in_yielded_event(
    advisor, user_with_telegram, list_bonsai_func, send_telegram_func
):
    import json

    results = await _collect(
        run_weekend_plan_reminders(
            advisor=advisor,
            list_all_user_settings_func=lambda: [user_with_telegram],
            list_planned_works_in_date_range_func=lambda **_: [],
            list_bonsai_func=list_bonsai_func,
            send_telegram_message_func=send_telegram_func,
        )
    )

    event = json.loads(results[0])
    assert event["response"] == "Weekend plan summary", (
        f"Expected advisor response text in yielded event, but got: {event}"
    )


@pytest.fixture
def advisor():
    mock_response = MagicMock()
    mock_response.text = "Weekend plan summary"
    mock = AsyncMock(return_value=mock_response)
    return mock


@pytest.fixture
def user_with_telegram():
    return UserSettings(user_id="u1", telegram_chat_id="chat-123")


@pytest.fixture
def list_bonsai_func():
    return lambda: []


@pytest.fixture
def send_telegram_func():
    return AsyncMock()
