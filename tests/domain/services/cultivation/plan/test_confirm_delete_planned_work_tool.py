import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.confirm_delete_planned_work_tool import (
    create_confirm_delete_planned_work_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_planned_work_not_found(delete_tool, tool_context):
    result = await delete_tool(planned_work_id=999, tool_context=tool_context)

    assert result == {"status": "error", "message": "planned_work_not_found"}, \
        "Non-existent work_id should return a not_found error"


@pytest.mark.asyncio
async def should_delete_with_correct_work_id_when_user_confirms(delete_tool, tool_context, captured_delete):
    await delete_tool(planned_work_id=1, tool_context=tool_context)

    assert captured_delete["work_id"] == 1, \
        "Should pass the correct work_id to delete_planned_work_func"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_work(tool_context, get_planned_work_func, delete_planned_work_func, planned_work_stub, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(work):
        captured_calls.append(work)
        return "confirmation text"

    tool = create_confirm_delete_planned_work_tool(
        get_planned_work_func, delete_planned_work_func, ask_confirmation_confirm, build_confirmation_message
    )
    await tool(planned_work_id=1, tool_context=tool_context)

    assert captured_calls == [planned_work_stub], \
        "build_confirmation_message should be called with the retrieved PlannedWork"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(delete_tool, tool_context):
    result = await delete_tool(planned_work_id=1, tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_delete_when_user_cancels(tool_context, captured_delete, get_planned_work_func, delete_planned_work_func, build_confirmation_message):
    tool = create_confirm_delete_planned_work_tool(
        get_planned_work_func, delete_planned_work_func, ask_confirmation_cancel, build_confirmation_message
    )
    await tool(planned_work_id=1, tool_context=tool_context)

    assert captured_delete == {}, \
        "delete_planned_work_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_planned_work_func, delete_planned_work_func, build_confirmation_message):
    tool = create_confirm_delete_planned_work_tool(
        get_planned_work_func, delete_planned_work_func, ask_confirmation_cancel, build_confirmation_message
    )
    result = await tool(planned_work_id=1, tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_delete():
    return {}


@pytest.fixture
def planned_work_stub():
    work = PlannedWork(
        bonsai_id=10,
        work_type="fertilizer_application",
        payload={"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"},
        scheduled_date="2026-03-15",
    )
    work.id = 1
    return work


@pytest.fixture
def get_planned_work_func(planned_work_stub):
    def get_planned_work(work_id: int):
        return None if work_id == 999 else planned_work_stub

    return get_planned_work


@pytest.fixture
def delete_planned_work_func(captured_delete):
    def delete_planned_work(work_id: int) -> None:
        captured_delete["work_id"] = work_id

    return delete_planned_work


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
        return f"Confirm deletion of work {work.id}"

    return build


@pytest.fixture
def delete_tool(get_planned_work_func, delete_planned_work_func, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_delete_planned_work_tool(
        get_planned_work_func=get_planned_work_func,
        delete_planned_work_func=delete_planned_work_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
