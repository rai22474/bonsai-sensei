import pytest

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_update_phytosanitary_tool import (
    create_confirm_update_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(update_tool, tool_context):
    result = await update_tool(name="", summary="Update product", usage_sheet="New instructions", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_name_required"}, \
        "Missing name should return a phytosanitary_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_not_found(update_tool_not_found, tool_context):
    result = await update_tool_not_found(name="Neem Oil", summary="Update Neem Oil", usage_sheet="New instructions", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_not_found"}, \
        "Non-existent product should return a phytosanitary_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = await update_tool(name="Neem Oil", summary="Update Neem Oil", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_update_required"}, \
        "No update fields should return a phytosanitary_update_required error"


@pytest.mark.asyncio
async def should_update_with_correct_name_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="Neem Oil", summary="Update Neem Oil", usage_sheet="New instructions", tool_context=tool_context)

    assert captured_update["name"] == "Neem Oil", \
        "Should pass the correct name to update_phytosanitary_func"


@pytest.mark.asyncio
async def should_update_with_correct_usage_sheet_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="Neem Oil", summary="Update Neem Oil", usage_sheet="New instructions", tool_context=tool_context)

    assert captured_update["phytosanitary_data"]["usage_sheet"] == "New instructions", \
        "Should include the new usage_sheet in phytosanitary_data"


@pytest.mark.asyncio
async def should_update_with_target_mapped_to_recommended_for_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(name="Neem Oil", summary="Update Neem Oil target", target="Aphids", tool_context=tool_context)

    assert captured_update["phytosanitary_data"]["recommended_for"] == "Aphids", \
        "Should map target to recommended_for in phytosanitary_data"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(update_tool, tool_context):
    result = await update_tool(name="Neem Oil", summary="Update Neem Oil", usage_sheet="New instructions", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_update_when_user_cancels(tool_context, captured_update, update_phytosanitary_func, get_phytosanitary_by_name_func):
    tool = create_confirm_update_phytosanitary_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, ask_confirmation_cancel)
    await tool(name="Neem Oil", summary="Update Neem Oil", usage_sheet="New instructions", tool_context=tool_context)

    assert captured_update == {}, \
        "update_phytosanitary_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, update_phytosanitary_func, get_phytosanitary_by_name_func):
    tool = create_confirm_update_phytosanitary_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, ask_confirmation_cancel)
    result = await tool(name="Neem Oil", summary="Update Neem Oil", usage_sheet="New instructions", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


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
        return Phytosanitary(name=name, usage_sheet="Sheet", recommended_for="Plagas")

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
def update_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, ask_confirmation_confirm):
    return create_confirm_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        ask_confirmation=ask_confirmation_confirm,
    )


@pytest.fixture
def update_tool_not_found(update_phytosanitary_func, get_phytosanitary_by_name_not_found, ask_confirmation_confirm):
    return create_confirm_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_not_found,
        ask_confirmation=ask_confirmation_confirm,
    )
