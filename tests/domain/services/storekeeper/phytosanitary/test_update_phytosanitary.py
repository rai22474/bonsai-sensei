import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.update_phytosanitary import (
    create_update_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(update_tool, tool_context):
    result = await update_tool(name="", recommended_amount="2 ml/L", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Missing name should return a phytosanitary_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_recommended_amount_is_missing(update_tool, tool_context):
    result = await update_tool(name="Neem Oil", recommended_amount="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "recommended_amount_required"}),
        "Missing recommended_amount should return a recommended_amount_required error")


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_not_found(update_tool_not_found, tool_context):
    result = await update_tool_not_found(name="Neem Oil", recommended_amount="2 ml/L", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "phytosanitary_not_found"}),
        "Non-existent product should return a phytosanitary_not_found error")


@pytest.mark.asyncio
async def should_update_with_given_recommended_amount_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="Neem Oil", recommended_amount="2 ml/L", tool_context=tool_context)

    assert_that(captured_update["phytosanitary_data"]["recommended_amount"], equal_to("2 ml/L"),
        "Should update with the provided recommended_amount")


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(update_tool, tool_context):
    result = await update_tool(name="Neem Oil", recommended_amount="2 ml/L", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_update_when_user_cancels(tool_context, captured_update, update_phytosanitary_func, get_phytosanitary_by_name_func, build_confirmation_message):
    tool = create_update_phytosanitary_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(name="Neem Oil", recommended_amount="2 ml/L", tool_context=tool_context)

    assert_that(captured_update, equal_to({}),
        "update_phytosanitary_func should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, update_phytosanitary_func, get_phytosanitary_by_name_func, build_confirmation_message):
    tool = create_update_phytosanitary_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(name="Neem Oil", recommended_amount="2 ml/L", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_phytosanitary_func(captured_update):
    def update_phytosanitary(name: str, phytosanitary_data: dict) -> None:
        captured_update["name"] = name
        captured_update["phytosanitary_data"] = phytosanitary_data

    return update_phytosanitary


@pytest.fixture
def get_phytosanitary_by_name_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return Phytosanitary(name=name, recommended_amount="5 ml/L")

    return get_phytosanitary_by_name


@pytest.fixture
def get_phytosanitary_by_name_not_found():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return None

    return get_phytosanitary_by_name


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
        return f"Confirm update phytosanitary '{name}' to '{recommended_amount}'"

    return build


@pytest.fixture
def update_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def update_tool_not_found(update_phytosanitary_func, get_phytosanitary_by_name_not_found, ask_confirmation_confirm, build_confirmation_message):
    return create_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_not_found,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
