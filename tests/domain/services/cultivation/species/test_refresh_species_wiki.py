import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.cultivation.species.refresh_species_wiki import (
    create_refresh_species_wiki_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_name_is_missing(refresh_tool, tool_context):
    result = await refresh_tool(name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_name_required"}, \
        "Missing name should return a species_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_species_not_found(refresh_tool_not_found, tool_context):
    result = await refresh_tool_not_found(name="Ficus Retusa", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_not_found"}, \
        "Non-existent species should return a species_not_found error"


@pytest.mark.asyncio
async def should_call_wiki_page_builder_with_common_and_scientific_name(refresh_tool, tool_context, captured_wiki_build):
    await refresh_tool(name="Ficus Retusa", tool_context=tool_context)

    assert captured_wiki_build["called_with"] == ("Ficus Retusa", "Ficus retusa"), \
        "wiki_page_builder should be called with common and scientific name"


@pytest.mark.asyncio
async def should_pass_instructions_to_wiki_page_builder(refresh_tool, tool_context, captured_wiki_build):
    await refresh_tool(name="Ficus Retusa", instructions="profundiza en cuidados por estación", tool_context=tool_context)

    assert captured_wiki_build["user_instructions"] == "profundiza en cuidados por estación", \
        "user instructions should be forwarded to wiki_page_builder"


@pytest.mark.asyncio
async def should_update_wiki_path_when_confirmed(refresh_tool, tool_context, captured_update):
    await refresh_tool(name="Ficus Retusa", tool_context=tool_context)

    assert captured_update["species_data"] == {"wiki_path": "species/ficus-retusa.md"}, \
        "Should update wiki_path with the path returned by wiki_page_builder"


@pytest.mark.asyncio
async def should_return_success_when_confirmed(refresh_tool, tool_context):
    result = await refresh_tool(name="Ficus Retusa", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_call_wiki_builder_when_cancelled(tool_context, captured_wiki_build, get_species_by_name_func, update_species_func, build_confirmation_message):
    tool = create_refresh_species_wiki_tool(
        get_species_by_name_func=get_species_by_name_func,
        update_species_func=update_species_func,
        wiki_page_builder=_wiki_page_builder(captured_wiki_build),
        ask_confirmation=ask_confirmation_cancel,
        build_confirmation_message=build_confirmation_message,
    )
    await tool(name="Ficus Retusa", tool_context=tool_context)

    assert "called_with" not in captured_wiki_build, \
        "wiki_page_builder should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_species_by_name_func, update_species_func, build_confirmation_message):
    tool = create_refresh_species_wiki_tool(
        get_species_by_name_func=get_species_by_name_func,
        update_species_func=update_species_func,
        wiki_page_builder=_wiki_page_builder({}),
        ask_confirmation=ask_confirmation_cancel,
        build_confirmation_message=build_confirmation_message,
    )
    result = await tool(name="Ficus Retusa", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


def _wiki_page_builder(captured):
    async def wiki_page_builder(common_name, scientific_name, user_instructions=""):
        captured["called_with"] = (common_name, scientific_name)
        captured["user_instructions"] = user_instructions
        return "species/ficus-retusa.md"
    return wiki_page_builder


@pytest.fixture
def captured_wiki_build():
    return {}


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_species_func(captured_update):
    def update_species(species_id: int, species_data: dict) -> None:
        captured_update["species_id"] = species_id
        captured_update["species_data"] = species_data
    return update_species


@pytest.fixture
def get_species_by_name_func():
    def get_species_by_name(name: str) -> Species | None:
        return Species(id=1, name=name, scientific_name="Ficus retusa", wiki_path="species/ficus-retusa.md")
    return get_species_by_name


@pytest.fixture
def get_species_by_name_not_found():
    def get_species_by_name(name: str) -> Species | None:
        return None
    return get_species_by_name


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def build_confirmation_message():
    def build(name):
        return f"Confirm wiki refresh for '{name}'"
    return build


@pytest.fixture
def refresh_tool(captured_wiki_build, update_species_func, get_species_by_name_func, build_confirmation_message):
    async def ask_confirmation(question, tool_context=None):
        return True
    return create_refresh_species_wiki_tool(
        get_species_by_name_func=get_species_by_name_func,
        update_species_func=update_species_func,
        wiki_page_builder=_wiki_page_builder(captured_wiki_build),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def refresh_tool_not_found(captured_wiki_build, update_species_func, get_species_by_name_not_found, build_confirmation_message):
    async def ask_confirmation(question, tool_context=None):
        return True
    return create_refresh_species_wiki_tool(
        get_species_by_name_func=get_species_by_name_not_found,
        update_species_func=update_species_func,
        wiki_page_builder=_wiki_page_builder(captured_wiki_build),
        ask_confirmation=ask_confirmation,
        build_confirmation_message=build_confirmation_message,
    )
