from datetime import date

import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.garden.execute_planned_work import (
    create_execute_planned_work_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_work_id_is_zero(execute_planned_work_tool, tool_context):
    result = await execute_planned_work_tool(work_id=0, tool_context=tool_context)

    assert result == {"status": "error", "message": "work_id_required"}, \
        "Zero work_id should return work_id_required error"


@pytest.mark.asyncio
async def should_return_error_when_planned_work_not_found(execute_planned_work_tool, tool_context):
    result = await execute_planned_work_tool(work_id=999, tool_context=tool_context)

    assert result == {"status": "error", "message": "planned_work_not_found"}, \
        "Unknown work_id should return planned_work_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, ask_confirmation_confirm, existing_planned_work):
    captured_calls = []

    def build_confirmation_message(work):
        captured_calls.append(work)
        return "confirmation text"

    tool = create_execute_planned_work_tool(get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(work_id=1, tool_context=tool_context)

    assert captured_calls == [existing_planned_work], \
        "build_confirmation_message should be called with the resolved PlannedWork entity"


@pytest.mark.asyncio
async def should_record_event_with_correct_type_when_user_confirms(execute_planned_work_tool, tool_context, captured_events):
    await execute_planned_work_tool(work_id=1, tool_context=tool_context)

    assert captured_events[0].event_type == "fertilizer_application", \
        "Should record a fertilizer_application event when user confirms"


@pytest.mark.asyncio
async def should_delete_planned_work_when_user_confirms(execute_planned_work_tool, tool_context, deleted_work_ids):
    await execute_planned_work_tool(work_id=1, tool_context=tool_context)

    assert deleted_work_ids == [1], \
        "Should delete the planned work when user confirms"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(execute_planned_work_tool, tool_context):
    result = await execute_planned_work_tool(work_id=1, tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_record_event_when_user_cancels(tool_context, captured_events, get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, build_confirmation_message):
    tool = create_execute_planned_work_tool(get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(work_id=1, tool_context=tool_context)

    assert captured_events == [], \
        "record_bonsai_event_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, build_confirmation_message):
    tool = create_execute_planned_work_tool(get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(work_id=1, tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_events():
    return []


@pytest.fixture
def deleted_work_ids():
    return []


@pytest.fixture
def record_bonsai_event_func(captured_events):
    def record_bonsai_event(bonsai_event: BonsaiEvent) -> BonsaiEvent:
        captured_events.append(bonsai_event)
        return bonsai_event

    return record_bonsai_event


@pytest.fixture
def delete_planned_work_func(deleted_work_ids):
    def delete_planned_work(work_id: int) -> bool:
        deleted_work_ids.append(work_id)
        return True

    return delete_planned_work


@pytest.fixture
def existing_planned_work():
    return PlannedWork(
        id=1,
        bonsai_id=10,
        work_type="fertilizer_application",
        payload={"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"},
        scheduled_date=date(2026, 3, 15),
    )


@pytest.fixture
def get_planned_work_func(existing_planned_work):
    def get_planned_work(work_id: int) -> PlannedWork | None:
        return existing_planned_work if work_id == existing_planned_work.id else None

    return get_planned_work


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def ask_confirmation_confirm():
    async def ask_confirmation(question, tool_context=None):
        return True

    return ask_confirmation


@pytest.fixture
def build_confirmation_message():
    def build(work):
        return f"Confirm execute planned work {work.id} ({work.work_type})"

    return build


@pytest.fixture
def execute_planned_work_tool(get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, ask_confirmation_confirm, build_confirmation_message):
    return create_execute_planned_work_tool(get_planned_work_func, record_bonsai_event_func, delete_planned_work_func, ask_confirmation_confirm, build_confirmation_message)
