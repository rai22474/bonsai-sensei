import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.update_fertilizer import (
    create_update_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(update_tool, tool_context):
    result = await update_tool(name="", recommended_amount="10 ml/L", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Missing name should return a fertilizer_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_recommended_amount_is_missing(update_tool, tool_context):
    result = await update_tool(name="GreenBoom", recommended_amount="", tool_context=tool_context)

    assert result == {"status": "error", "message": "recommended_amount_required"}, \
        "Missing recommended_amount should return a recommended_amount_required error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(update_tool_not_found, tool_context):
    result = await update_tool_not_found(name="GreenBoom", recommended_amount="10 ml/L", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_not_found"}, \
        "Non-existent fertilizer should return a fertilizer_not_found error"


@pytest.mark.asyncio
async def should_update_with_given_recommended_amount_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="GreenBoom", recommended_amount="10 ml/L", tool_context=tool_context)

    assert captured_update["fertilizer_data"]["recommended_amount"] == "10 ml/L", \
        "Should update with the provided recommended_amount"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(update_tool, tool_context):
    result = await update_tool(name="GreenBoom", recommended_amount="10 ml/L", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_update_when_user_cancels(tool_context, captured_update, update_fertilizer_func, get_fertilizer_by_name_func, build_confirmation_message):
    tool = create_update_fertilizer_tool(update_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(name="GreenBoom", recommended_amount="10 ml/L", tool_context=tool_context)

    assert captured_update == {}, \
        "update_fertilizer_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, update_fertilizer_func, get_fertilizer_by_name_func, build_confirmation_message):
    tool = create_update_fertilizer_tool(update_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(name="GreenBoom", recommended_amount="10 ml/L", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


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
        return Fertilizer(name=name, recommended_amount="5 ml/L")

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
def build_confirmation_message():
    def build(name, recommended_amount):
        return f"Confirm update fertilizer '{name}' to '{recommended_amount}'"

    return build


@pytest.fixture
def update_tool(update_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def update_tool_not_found(update_fertilizer_func, get_fertilizer_by_name_not_found, ask_confirmation_confirm, build_confirmation_message):
    return create_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_not_found,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
