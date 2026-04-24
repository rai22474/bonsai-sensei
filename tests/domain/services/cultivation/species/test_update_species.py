import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.cultivation.species.update_species import (
    create_update_species_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_species_name_is_missing(update_tool, tool_context):
    result = await update_tool(species={"scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert result == {"status": "error", "message": "species_name_required"}, \
        "species dict without name or common_name should return a species_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = await update_tool(species={"name": "Elm"}, tool_context=tool_context)

    assert result == {"status": "error", "message": "species_update_required"}, \
        "species dict with only the identifier and no update fields should return a species_update_required error"


@pytest.mark.asyncio
async def should_return_error_when_species_not_found(update_tool, tool_context):
    result = await update_tool(species={"name": "Unknown", "scientific_name": "Unknownus"}, tool_context=tool_context)

    assert result == {"status": "error", "message": "species_not_found"}, \
        "Unknown species name should return a species_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, update_species_func, get_species_by_name_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(species_name, species_data):
        captured_calls.append((species_name, species_data))
        return "confirmation text"

    tool = create_update_species_tool(update_species_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(species={"name": "Elm", "scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert captured_calls == [("Elm", {"scientific_name": "Ulmus minor"})], \
        "build_confirmation_message should be called with species_name and resolved species_data"


@pytest.mark.asyncio
async def should_update_with_correct_species_id_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(species={"name": "Elm", "scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert captured_update["species_id"] == 1, \
        "Should pass the existing species id to update_species_func"


@pytest.mark.asyncio
async def should_update_with_scientific_name_in_species_data_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(species={"name": "Elm", "scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert captured_update["species_data"]["scientific_name"] == "Ulmus minor", \
        "Should include scientific_name in species_data"


@pytest.mark.asyncio
async def should_update_with_common_name_mapped_to_name_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(species={"name": "Elm", "common_name": "English Elm"}, tool_context=tool_context)

    assert captured_update["species_data"]["name"] == "English Elm", \
        "Should map common_name to 'name' in species_data"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(update_tool, tool_context):
    result = await update_tool(species={"name": "Elm", "scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_update_when_user_cancels(tool_context, captured_update, update_species_func, get_species_by_name_func, build_confirmation_message):
    tool = create_update_species_tool(update_species_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(species={"name": "Elm", "scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert captured_update == {}, \
        "update_species_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, update_species_func, get_species_by_name_func, build_confirmation_message):
    tool = create_update_species_tool(update_species_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(species={"name": "Elm", "scientific_name": "Ulmus minor"}, tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


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
    def build(species_name, species_data):
        return f"Confirm update species '{species_name}': {species_data}"

    return build


@pytest.fixture
def update_tool(update_species_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_update_species_tool(update_species_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
