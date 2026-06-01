import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.create_fertilizer import (
    create_create_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(create_tool, tool_context):
    result = await create_tool(name="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "fertilizer_name_required"}),
        "Missing name should return a fertilizer_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_already_exists(create_tool_with_existing, tool_context):
    result = await create_tool_with_existing(name="GreenBoom", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "fertilizer_already_exists"}),
        "Existing fertilizer should return a fertilizer_already_exists error")


@pytest.mark.asyncio
async def should_build_confirmation_message_with_name_only(tool_context, create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(name):
        captured_calls.append(name)
        return "confirmation text"

    tool = create_create_fertilizer_tool(create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message)
    await tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_calls, equal_to(["GreenBoom"]),
        "build_confirmation_message should be called with name only")


@pytest.mark.asyncio
async def should_create_with_correct_name_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_create["fertilizer"].name, equal_to("GreenBoom"),
        "Should pass the correct name to create_fertilizer_func")


@pytest.mark.asyncio
async def should_create_with_wiki_path_from_builder_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_create["fertilizer"].wiki_path, equal_to("fertilizers/greenboom.md"),
        "Should store the wiki_path returned by the wiki_page_builder")


@pytest.mark.asyncio
async def should_create_with_recommended_amount_from_builder_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_create["fertilizer"].recommended_amount, equal_to("5 ml/L"),
        "Should store the recommended_amount extracted by the wiki_page_builder")


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(create_tool, tool_context):
    result = await create_tool(name="GreenBoom", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_create, create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, build_confirmation_message):
    tool = create_create_fertilizer_tool(create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, ask_confirmation_cancel, build_confirmation_message)
    await tool(name="GreenBoom", tool_context=tool_context)

    assert_that(captured_create, equal_to({}),
        "create_fertilizer_func should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, build_confirmation_message):
    tool = create_create_fertilizer_tool(create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(name="GreenBoom", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_create():
    return {}


@pytest.fixture
def create_fertilizer_func(captured_create):
    def create_fertilizer(fertilizer) -> None:
        captured_create["fertilizer"] = fertilizer

    return create_fertilizer


@pytest.fixture
def wiki_page_builder():
    async def build(name: str) -> tuple[str, str]:
        slug = name.lower().replace(" ", "-")
        return f"fertilizers/{slug}.md", "5 ml/L"

    return build


@pytest.fixture
def get_fertilizer_by_name_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return None

    return get_fertilizer_by_name


@pytest.fixture
def existing_fertilizer_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return Fertilizer(name=name, recommended_amount="5 ml/L")

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
        return f"Confirm create fertilizer '{name}'"

    return build


@pytest.fixture
def create_tool(create_fertilizer_func, get_fertilizer_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def create_tool_with_existing(create_fertilizer_func, existing_fertilizer_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        get_fertilizer_by_name_func=existing_fertilizer_func,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
