import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.create_phytosanitary import (
    create_create_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(create_tool, tool_context):
    result = await create_tool(name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_name_required"}, \
        "Missing name should return a phytosanitary_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_already_exists(create_tool_with_existing, tool_context):
    result = await create_tool_with_existing(name="Neem Oil", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_already_exists"}, \
        "Existing product should return a phytosanitary_already_exists error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_name_only(tool_context, create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(name):
        captured_calls.append(name)
        return "confirmation text"

    tool = create_create_phytosanitary_tool(create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message)
    await tool(name="Neem Oil", tool_context=tool_context)

    assert captured_calls == ["Neem Oil"], \
        "build_confirmation_message should be called with name only"


@pytest.mark.asyncio
async def should_create_with_correct_name_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="Neem Oil", tool_context=tool_context)

    assert captured_create["phytosanitary"].name == "Neem Oil", \
        "Should pass the correct name to create_phytosanitary_func"


@pytest.mark.asyncio
async def should_create_with_wiki_path_from_builder_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="Neem Oil", tool_context=tool_context)

    assert captured_create["phytosanitary"].wiki_path == "phytosanitaries/neem-oil.md", \
        "Should store the wiki_path returned by the wiki_page_builder"


@pytest.mark.asyncio
async def should_create_with_recommended_amount_from_builder_when_user_confirms(create_tool, tool_context, captured_create):
    await create_tool(name="Neem Oil", tool_context=tool_context)

    assert captured_create["phytosanitary"].recommended_amount == "5 ml/L", \
        "Should store the recommended_amount extracted by the wiki_page_builder"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(create_tool, tool_context):
    result = await create_tool(name="Neem Oil", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_create, create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, build_confirmation_message):
    tool = create_create_phytosanitary_tool(create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, ask_confirmation_cancel, build_confirmation_message)
    await tool(name="Neem Oil", tool_context=tool_context)

    assert captured_create == {}, \
        "create_phytosanitary_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, build_confirmation_message):
    tool = create_create_phytosanitary_tool(create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(name="Neem Oil", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_create():
    return {}


@pytest.fixture
def create_phytosanitary_func(captured_create):
    def create_phytosanitary(phytosanitary) -> None:
        captured_create["phytosanitary"] = phytosanitary

    return create_phytosanitary


@pytest.fixture
def wiki_page_builder():
    async def build(name: str) -> tuple[str, str]:
        slug = name.lower().replace(" ", "-")
        return f"phytosanitaries/{slug}.md", "5 ml/L"

    return build


@pytest.fixture
def get_phytosanitary_by_name_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return None

    return get_phytosanitary_by_name


@pytest.fixture
def existing_phytosanitary_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return Phytosanitary(name=name, recommended_amount="5 ml/L")

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
    def build(name):
        return f"Confirm create phytosanitary '{name}'"

    return build


@pytest.fixture
def create_tool(create_phytosanitary_func, get_phytosanitary_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_create_phytosanitary_tool(
        create_phytosanitary_func=create_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def create_tool_with_existing(create_phytosanitary_func, existing_phytosanitary_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_create_phytosanitary_tool(
        create_phytosanitary_func=create_phytosanitary_func,
        get_phytosanitary_by_name_func=existing_phytosanitary_func,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
