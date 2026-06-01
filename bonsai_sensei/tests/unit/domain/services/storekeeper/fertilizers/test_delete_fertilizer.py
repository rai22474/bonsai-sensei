import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.delete_fertilizer import (
    create_delete_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(delete_tool, tool_context):
    result = await delete_tool(name="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "fertilizer_name_required"}),
        "Missing name should return a fertilizer_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(delete_tool_not_found, tool_context):
    result = await delete_tool_not_found(name="GreenBoom", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "fertilizer_not_found"}),
        "Non-existent fertilizer should return a fertilizer_not_found error")


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(name):
        captured_calls.append(name)
        return "confirmation text"

    tool = create_delete_fertilizer_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_calls, equal_to(["GreenBoom"]),
        "build_confirmation_message should be called with the fertilizer name")


@pytest.mark.asyncio
async def should_delete_with_correct_name_when_user_confirms(delete_tool, tool_context, captured_delete):
    await delete_tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_delete["name"], equal_to("GreenBoom"),
        "Should pass the correct name to delete_fertilizer_func")


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(delete_tool, tool_context):
    result = await delete_tool(name="GreenBoom", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_delete_when_user_cancels(tool_context, captured_delete, delete_fertilizer_func, get_fertilizer_by_name_func, build_confirmation_message):
    tool = create_delete_fertilizer_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_delete, equal_to({}),
        "delete_fertilizer_func should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, delete_fertilizer_func, get_fertilizer_by_name_func, build_confirmation_message):
    tool = create_delete_fertilizer_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(name="GreenBoom", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


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
def build_confirmation_message():
    def build(name):
        return f"Confirm delete fertilizer '{name}'"

    return build


@pytest.fixture
def delete_tool(delete_fertilizer_func, get_fertilizer_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_delete_fertilizer_tool(
        delete_fertilizer_func=delete_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def delete_tool_not_found(delete_fertilizer_func, get_fertilizer_by_name_not_found, ask_confirmation_confirm, build_confirmation_message):
    return create_delete_fertilizer_tool(
        delete_fertilizer_func=delete_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_not_found,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
