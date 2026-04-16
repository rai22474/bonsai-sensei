import pytest

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_delete_fertilizer_tool import (
    create_confirm_delete_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(delete_tool, tool_context):
    result = await delete_tool(name="", summary="Delete fertilizer", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Missing name should return a fertilizer_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(delete_tool_not_found, tool_context):
    result = await delete_tool_not_found(name="GreenBoom", summary="Delete GreenBoom", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_not_found"}, \
        "Non-existent fertilizer should return a fertilizer_not_found error"


@pytest.mark.asyncio
async def should_delete_with_correct_name_when_user_confirms(delete_tool, tool_context, captured_delete):
    await delete_tool(name="GreenBoom", summary="Delete GreenBoom", tool_context=tool_context)

    assert captured_delete["name"] == "GreenBoom", \
        "Should pass the correct name to delete_fertilizer_func"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(delete_tool, tool_context):
    result = await delete_tool(name="GreenBoom", summary="Delete GreenBoom", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_delete_when_user_cancels(tool_context, captured_delete, delete_fertilizer_func, get_fertilizer_by_name_func):
    tool = create_confirm_delete_fertilizer_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel)
    await tool(name="GreenBoom", summary="Delete GreenBoom", tool_context=tool_context)

    assert captured_delete == {}, \
        "delete_fertilizer_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, delete_fertilizer_func, get_fertilizer_by_name_func):
    tool = create_confirm_delete_fertilizer_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel)
    result = await tool(name="GreenBoom", summary="Delete GreenBoom", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


@pytest.fixture
def captured_delete():
    return {}


@pytest.fixture
def delete_fertilizer_func(captured_delete):
    def delete_fertilizer(name: str) -> None:
        captured_delete["name"] = name

    return delete_fertilizer


@pytest.fixture
def get_fertilizer_by_name_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return Fertilizer(name=name, usage_sheet="Sheet", recommended_amount="5 ml/L")

    return get_fertilizer_by_name


@pytest.fixture
def get_fertilizer_by_name_not_found():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return None

    return get_fertilizer_by_name


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def ask_confirmation_confirm():
    async def ask_confirmation(question, tool_context=None):
        return True

    return ask_confirmation


@pytest.fixture
def delete_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_confirm):
    return create_confirm_delete_fertilizer_tool(
        delete_fertilizer_func=delete_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        ask_confirmation=ask_confirmation_confirm,
    )


@pytest.fixture
def delete_tool_not_found(delete_fertilizer_func, get_fertilizer_by_name_not_found, ask_confirmation_confirm):
    return create_confirm_delete_fertilizer_tool(
        delete_fertilizer_func=delete_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_not_found,
        ask_confirmation=ask_confirmation_confirm,
    )
