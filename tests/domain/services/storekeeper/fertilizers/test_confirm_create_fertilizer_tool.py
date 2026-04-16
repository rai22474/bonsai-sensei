import pytest

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_create_fertilizer_tool import (
    create_confirm_create_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(create_tool, tool_context):
    result = await create_tool(name="", summary="Create fertilizer", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Missing name should return a fertilizer_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_already_exists(create_tool_with_existing, tool_context):
    result = await create_tool_with_existing(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_already_exists"}, \
        "Existing fertilizer should return a fertilizer_already_exists error"


@pytest.mark.asyncio
async def should_create_with_correct_name_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert captured_create["fertilizer"].name == "GreenBoom", \
        "Should pass the correct name to create_fertilizer_func"


@pytest.mark.asyncio
async def should_create_with_usage_sheet_from_searcher_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert captured_create["fertilizer"].usage_sheet == "Apply 5 ml per litre of water.", \
        "Should pass the usage_sheet returned by the searcher"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(create_tool, tool_context):
    result = await create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_create, create_fertilizer_func, get_fertilizer_by_name_func, searcher):
    tool = create_confirm_create_fertilizer_tool(create_fertilizer_func, get_fertilizer_by_name_func, searcher, ask_confirmation_cancel)
    await tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert captured_create == {}, \
        "create_fertilizer_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, create_fertilizer_func, get_fertilizer_by_name_func, searcher):
    tool = create_confirm_create_fertilizer_tool(create_fertilizer_func, get_fertilizer_by_name_func, searcher, ask_confirmation_cancel)
    result = await tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


@pytest.fixture
def captured_create():
    return {}


@pytest.fixture
def create_fertilizer_func(captured_create):
    def create_fertilizer(fertilizer) -> None:
        captured_create["fertilizer"] = fertilizer

    return create_fertilizer


@pytest.fixture
def searcher():
    def search(query: str) -> dict:
        return {"answer": "Apply 5 ml per litre of water.", "results": []}

    return search


@pytest.fixture
def get_fertilizer_by_name_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return None

    return get_fertilizer_by_name


@pytest.fixture
def existing_fertilizer_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return Fertilizer(name=name, usage_sheet="Old sheet", recommended_amount="5 ml/L")

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
def create_tool(create_fertilizer_func, get_fertilizer_by_name_func, searcher, ask_confirmation_confirm):
    return create_confirm_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        searcher=searcher,
        ask_confirmation=ask_confirmation_confirm,
    )


@pytest.fixture
def create_tool_with_existing(create_fertilizer_func, existing_fertilizer_func, searcher, ask_confirmation_confirm):
    return create_confirm_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        get_fertilizer_by_name_func=existing_fertilizer_func,
        searcher=searcher,
        ask_confirmation=ask_confirmation_confirm,
    )
