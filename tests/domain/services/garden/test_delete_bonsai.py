import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.garden.delete_bonsai import (
    create_delete_bonsai_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_id_is_missing(delete_tool, tool_context):
    result = await delete_tool(bonsai_id=0, bonsai_name="Naruto", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_id_required"}, \
        "Missing bonsai_id should return bonsai_id_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_missing(delete_tool, tool_context):
    result = await delete_tool(bonsai_id=1, bonsai_name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Missing bonsai_name should return bonsai_name_required error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, delete_bonsai_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_id, bonsai_name):
        captured_calls.append((bonsai_id, bonsai_name))
        return "confirmation text"

    tool = create_delete_bonsai_tool(delete_bonsai_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(bonsai_id=1, bonsai_name="Naruto", tool_context=tool_context)

    assert captured_calls == [(1, "Naruto")], \
        "build_confirmation_message should be called with bonsai_id and bonsai_name"


@pytest.mark.asyncio
async def should_execute_delete_when_user_confirms(delete_tool, tool_context, captured_delete):
    await delete_tool(bonsai_id=1, bonsai_name="Naruto", tool_context=tool_context)

    assert captured_delete.get("bonsai_id") == 1, \
        "delete_bonsai_func should be called with the correct bonsai_id when user confirms"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(delete_tool, tool_context):
    result = await delete_tool(bonsai_id=1, bonsai_name="Naruto", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_execute_delete_when_user_cancels(tool_context, captured_delete, delete_bonsai_func, build_confirmation_message):
    tool = create_delete_bonsai_tool(delete_bonsai_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(bonsai_id=1, bonsai_name="Naruto", tool_context=tool_context)

    assert "bonsai_id" not in captured_delete, \
        "delete_bonsai_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, delete_bonsai_func, build_confirmation_message):
    tool = create_delete_bonsai_tool(delete_bonsai_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(bonsai_id=1, bonsai_name="Naruto", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_delete():
    return {}


@pytest.fixture
def delete_bonsai_func(captured_delete):
    def delete_bonsai(bonsai_id: int) -> None:
        captured_delete["bonsai_id"] = bonsai_id

    return delete_bonsai


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
    def build(bonsai_id, bonsai_name):
        return f"Confirm delete bonsai '{bonsai_name}' (id={bonsai_id})"

    return build


@pytest.fixture
def delete_tool(delete_bonsai_func, ask_confirmation_confirm, build_confirmation_message):
    return create_delete_bonsai_tool(delete_bonsai_func, ask_confirmation_confirm, build_confirmation_message)
