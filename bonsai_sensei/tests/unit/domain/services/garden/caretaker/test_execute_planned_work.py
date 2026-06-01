from datetime import date

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.human_input import ConfirmationResult, SelectionNoneResult
from bonsai_sensei.domain.services.garden.caretaker.execute_planned_work import (
    create_execute_planned_work_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(tool_context):
    tool = _make_tool(get_bonsai_by_name_func=lambda name: None)

    result = await tool(bonsai_name="unknown", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_no_planned_works(tool_context, existing_bonsai):
    tool = _make_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai,
        list_planned_works_func=lambda bonsai_id: [],
    )

    result = await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "no_planned_works"}),
        "Bonsai with no planned works should return no_planned_works error")


@pytest.mark.asyncio
async def should_confirm_without_selection_when_single_work(tool, tool_context, captured_confirmations, existing_planned_work):
    await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(len(captured_confirmations), equal_to(1),
        "Should ask exactly one confirmation when there is a single planned work")


@pytest.mark.asyncio
async def should_ask_selection_when_multiple_works(tool_context, existing_bonsai, existing_planned_work, captured_selections):
    second_work = PlannedWork(
        id=2,
        bonsai_id=10,
        work_type="transplant",
        payload={},
        scheduled_date=date(2026, 4, 1),
    )
    tool = _make_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai,
        list_planned_works_func=lambda bonsai_id: [existing_planned_work, second_work],
        ask_selection=_ask_selection_capture(captured_selections, pick_index=0),
    )

    await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(len(captured_selections), equal_to(1),
        "Should present a selection question when multiple works are available")


@pytest.mark.asyncio
async def should_record_event_when_user_confirms(tool, tool_context, captured_events):
    await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(captured_events[0].event_type, equal_to("fertilizer_application"),
        "Should record a fertilizer_application event when user confirms")


@pytest.mark.asyncio
async def should_delete_planned_work_when_user_confirms(tool, tool_context, deleted_work_ids):
    await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(deleted_work_ids, equal_to([1]),
        "Should delete the planned work when user confirms")


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(tool, tool_context):
    result = await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_record_event_when_user_cancels(tool_context, existing_bonsai, existing_planned_work, captured_events):
    tool = _make_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai,
        list_planned_works_func=lambda bonsai_id: [existing_planned_work],
        ask_confirmation=_ask_confirmation_cancel,
        captured_events=captured_events,
    )

    await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(captured_events, equal_to([]),
        "record_bonsai_event_func should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, existing_bonsai, existing_planned_work):
    tool = _make_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai,
        list_planned_works_func=lambda bonsai_id: [existing_planned_work],
        ask_confirmation=_ask_confirmation_cancel,
    )

    result = await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_cancels_selection(tool_context, existing_bonsai, existing_planned_work):
    second_work = PlannedWork(
        id=2,
        bonsai_id=10,
        work_type="transplant",
        payload={},
        scheduled_date=date(2026, 4, 1),
    )

    async def ask_selection_cancel(question, options, tool_context=None, **kwargs):
        return SelectionNoneResult(reason="user_cancelled")

    tool = _make_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai,
        list_planned_works_func=lambda bonsai_id: [existing_planned_work, second_work],
        ask_selection=ask_selection_cancel,
    )

    result = await tool(bonsai_name="naruto", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled when user cancels selection")


def _make_tool(
    get_bonsai_by_name_func=None,
    list_planned_works_func=None,
    ask_confirmation=None,
    ask_selection=None,
    captured_events=None,
    deleted_ids=None,
):
    events = captured_events if captured_events is not None else []
    ids = deleted_ids if deleted_ids is not None else []

    return create_execute_planned_work_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func or (lambda name: None),
        list_planned_works_func=list_planned_works_func or (lambda bonsai_id: []),
        record_bonsai_event_func=lambda bonsai_event: events.append(bonsai_event),
        delete_planned_work_func=lambda work_id: ids.append(work_id),
        ask_confirmation=ask_confirmation or _ask_confirmation_confirm,
        ask_selection=ask_selection or _ask_selection_first,
        build_confirmation_message=lambda work, bonsai_name: f"Confirm {work.work_type}",
        build_selection_question=lambda bonsai_name: f"Select work for {bonsai_name}",
        build_work_option_label=lambda work: f"{work.work_type} – {work.scheduled_date}",
    )


def _ask_selection_capture(captured, pick_index=0):
    async def ask_selection(question, options, tool_context=None, **kwargs):
        captured.append(question)
        return options[pick_index]
    return ask_selection


async def _ask_selection_first(question, options, tool_context=None, **kwargs):
    return options[0]


async def _ask_confirmation_confirm(question, tool_context=None):
    return True


async def _ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_events():
    return []


@pytest.fixture
def deleted_work_ids():
    return []


@pytest.fixture
def captured_selections():
    return []


@pytest.fixture
def captured_confirmations():
    return []


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=10, name="naruto", species_id=1)


@pytest.fixture
def existing_planned_work():
    return PlannedWork(
        id=1,
        bonsai_id=10,
        work_type="fertilizer_application",
        payload={"fertilizer_id": 1, "fertilizer_name": "biogold", "amount": "5 ml"},
        scheduled_date=date(2026, 3, 15),
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def tool(existing_bonsai, existing_planned_work, captured_events, deleted_work_ids, captured_confirmations):
    async def ask_confirmation(question, tool_context=None):
        captured_confirmations.append(question)
        return True

    return create_execute_planned_work_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai,
        list_planned_works_func=lambda bonsai_id: [existing_planned_work],
        record_bonsai_event_func=lambda bonsai_event: captured_events.append(bonsai_event),
        delete_planned_work_func=lambda work_id: deleted_work_ids.append(work_id),
        ask_confirmation=ask_confirmation,
        ask_selection=_ask_selection_first,
        build_confirmation_message=lambda work, bonsai_name: f"Confirm {work.work_type} for {bonsai_name}",
        build_selection_question=lambda bonsai_name: f"Select work for {bonsai_name}",
        build_work_option_label=lambda work: f"{work.work_type} – {work.scheduled_date}",
    )
