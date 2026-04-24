import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.cultivation.species.confirm_delete_species_tool import (
    create_confirm_delete_species_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_species_name_is_empty(delete_tool, tool_context):
    result = await delete_tool(species_name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_name_required"}, \
        "Empty species name should return a species_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_species_not_found(delete_tool, tool_context):
    result = await delete_tool(species_name="Unknown", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_not_found"}, \
        "Unknown species name should return a species_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, delete_species_func, get_species_by_name_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(species_name):
        captured_calls.append(species_name)
        return "confirmation text"

    tool = create_confirm_delete_species_tool(delete_species_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(species_name="Elm", tool_context=tool_context)

    assert captured_calls == ["Elm"], \
        "build_confirmation_message should be called with the species name"


@pytest.mark.asyncio
async def should_delete_with_correct_species_id_when_user_confirms(delete_tool, tool_context, captured_delete):
    await delete_tool(species_name="Elm", tool_context=tool_context)

    assert captured_delete["species_id"] == 1, \
        "Should pass the existing species id to delete_species_func"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(delete_tool, tool_context):
    result = await delete_tool(species_name="Elm", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_delete_when_user_cancels(tool_context, captured_delete, delete_species_func, get_species_by_name_func, build_confirmation_message):
    tool = create_confirm_delete_species_tool(delete_species_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(species_name="Elm", tool_context=tool_context)

    assert captured_delete == {}, \
        "delete_species_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, delete_species_func, get_species_by_name_func, build_confirmation_message):
    tool = create_confirm_delete_species_tool(delete_species_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(species_name="Elm", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_delete():
    return {}


@pytest.fixture
def delete_species_func(captured_delete):
    def delete_species(species_id: int) -> None:
        captured_delete["species_id"] = species_id

    return delete_species


@pytest.fixture
def existing_species():
    return [
        Species(id=1, name="Elm", scientific_name="Ulmus", care_guide={}),
        Species(id=2, name="Oak", scientific_name="Quercus", care_guide={}),
    ]


@pytest.fixture
def get_species_by_name_func(existing_species):
    def get_species_by_name(name: str) -> Species | None:
        return next((species for species in existing_species if species.name == name), None)

    return get_species_by_name


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
    def build(species_name):
        return f"Confirm delete species '{species_name}'"

    return build


@pytest.fixture
def delete_tool(delete_species_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_delete_species_tool(delete_species_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
