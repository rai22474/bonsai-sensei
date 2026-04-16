import pytest

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_update_fertilizer_tool import (
    create_confirm_update_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(update_tool, tool_context):
    result = await update_tool(name="", summary="Update fertilizer", usage_sheet="New sheet", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Missing name should return a fertilizer_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(update_tool_not_found, tool_context):
    result = await update_tool_not_found(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_not_found"}, \
        "Non-existent fertilizer should return a fertilizer_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = await update_tool(name="GreenBoom", summary="Update GreenBoom", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_update_required"}, \
        "No update fields should return a fertilizer_update_required error"


@pytest.mark.asyncio
async def should_update_with_correct_name_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)

    assert captured_update["name"] == "GreenBoom", \
        "Should pass the correct name to update_fertilizer_func"


@pytest.mark.asyncio
async def should_update_with_correct_usage_sheet_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)

    assert captured_update["fertilizer_data"]["usage_sheet"] == "New sheet", \
        "Should include the new usage_sheet in fertilizer_data"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(update_tool, tool_context):
    result = await update_tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_update_when_user_cancels(tool_context, captured_update, update_fertilizer_func, get_fertilizer_by_name_func):
    tool = create_confirm_update_fertilizer_tool(update_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel)
    await tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)

    assert captured_update == {}, \
        "update_fertilizer_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, update_fertilizer_func, get_fertilizer_by_name_func):
    tool = create_confirm_update_fertilizer_tool(update_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel)
    result = await tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_fertilizer_func(captured_update):
    def update_fertilizer(name: str, fertilizer_data: dict) -> None:
        captured_update["name"] = name
        captured_update["fertilizer_data"] = fertilizer_data

    return update_fertilizer


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
def update_tool(update_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_confirm):
    return create_confirm_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        ask_confirmation=ask_confirmation_confirm,
    )


@pytest.fixture
def update_tool_not_found(update_fertilizer_func, get_fertilizer_by_name_not_found, ask_confirmation_confirm):
    return create_confirm_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_not_found,
        ask_confirmation=ask_confirmation_confirm,
    )
