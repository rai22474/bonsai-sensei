import pytest
from hamcrest import assert_that, equal_to, has_key, not_

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.storekeeper.phytosanitary.refresh_phytosanitary_wiki import (
    create_refresh_phytosanitary_wiki_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(refresh_tool, tool_context):
    result = await refresh_tool(name="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Missing name should return a phytosanitary_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_not_found(refresh_tool_not_found, tool_context):
    result = await refresh_tool_not_found(name="Neem Oil", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "phytosanitary_not_found"}),
        "Non-existent phytosanitary should return a phytosanitary_not_found error")


@pytest.mark.asyncio
async def should_call_wiki_page_builder_when_confirmed(refresh_tool, tool_context, captured_wiki_build):
    await refresh_tool(name="Neem Oil", tool_context=tool_context)

    assert_that(captured_wiki_build["called_with"], equal_to("Neem Oil"),
        "wiki_page_builder should be called with the phytosanitary name")


@pytest.mark.asyncio
async def should_pass_instructions_to_wiki_page_builder(refresh_tool, tool_context, captured_wiki_build):
    await refresh_tool(name="Neem Oil", instructions="amplía la sección de plagas objetivo", tool_context=tool_context)

    assert_that(captured_wiki_build["user_instructions"], equal_to("amplía la sección de plagas objetivo"),
        "user instructions should be forwarded to wiki_page_builder")


@pytest.mark.asyncio
async def should_update_wiki_path_and_recommended_amount_when_confirmed(refresh_tool, tool_context, captured_update):
    await refresh_tool(name="Neem Oil", tool_context=tool_context)

    assert_that(captured_update["phytosanitary_data"], equal_to({"wiki_path": "phytosanitaries/neem-oil.md", "recommended_amount": "2 ml/L"}),
        "Should update wiki_path and recommended_amount from wiki_page_builder output")


@pytest.mark.asyncio
async def should_return_success_when_confirmed(refresh_tool, tool_context):
    result = await refresh_tool(name="Neem Oil", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_call_wiki_builder_when_cancelled(tool_context, captured_wiki_build, get_phytosanitary_by_name_func, update_phytosanitary_func, build_confirmation_message):
    tool = create_refresh_phytosanitary_wiki_tool(
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        update_phytosanitary_func=update_phytosanitary_func,
        wiki_page_builder=_wiki_page_builder(captured_wiki_build),
        ask_confirmation=ask_confirmation_cancel,
        build_confirmation_message=build_confirmation_message,
    )
    await tool(name="Neem Oil", tool_context=tool_context)

    assert_that(captured_wiki_build, not_(has_key("called_with")),
        "wiki_page_builder should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_phytosanitary_by_name_func, update_phytosanitary_func, build_confirmation_message):
    tool = create_refresh_phytosanitary_wiki_tool(
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        update_phytosanitary_func=update_phytosanitary_func,
        wiki_page_builder=_wiki_page_builder({}),
        ask_confirmation=ask_confirmation_cancel,
        build_confirmation_message=build_confirmation_message,
    )
    result = await tool(name="Neem Oil", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


def _wiki_page_builder(captured):
    async def wiki_page_builder(name, user_instructions=""):
        captured["called_with"] = name
        captured["user_instructions"] = user_instructions
        return "phytosanitaries/neem-oil.md", "2 ml/L"
    return wiki_page_builder


@pytest.fixture
def captured_wiki_build():
    return {}


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
        return Phytosanitary(name=name, recommended_amount="1 ml/L")
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
def build_confirmation_message():
    def build(name):
        return f"Confirm wiki refresh for '{name}'"
    return build


@pytest.fixture
def refresh_tool(captured_wiki_build, update_phytosanitary_func, get_phytosanitary_by_name_func, build_confirmation_message):
    async def ask_confirmation(question, tool_context=None):
        return True
    return create_refresh_phytosanitary_wiki_tool(
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        update_phytosanitary_func=update_phytosanitary_func,
        wiki_page_builder=_wiki_page_builder(captured_wiki_build),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def refresh_tool_not_found(captured_wiki_build, update_phytosanitary_func, get_phytosanitary_by_name_not_found, build_confirmation_message):
    async def ask_confirmation(question, tool_context=None):
        return True
    return create_refresh_phytosanitary_wiki_tool(
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_not_found,
        update_phytosanitary_func=update_phytosanitary_func,
        wiki_page_builder=_wiki_page_builder(captured_wiki_build),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )
