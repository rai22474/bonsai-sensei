import pytest

from bonsai_sensei.domain.services.garden.confirm_update_bonsai_tool import (
    create_confirm_update_bonsai_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_id_is_missing(update_tool, tool_context):
    result = await update_tool(bonsai_id=0, bonsai_name="Naruto", tool_context=tool_context, name="New name")

    assert result == {"status": "error", "message": "bonsai_id_required"}, \
        "Missing bonsai_id should return bonsai_id_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_missing(update_tool, tool_context):
    result = await update_tool(bonsai_id=1, bonsai_name="", tool_context=tool_context, name="New name")

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Empty bonsai name should return bonsai_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = await update_tool(bonsai_id=1, bonsai_name="Naruto", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_update_required"}, \
        "No update fields should return bonsai_update_required error"


@pytest.mark.asyncio
async def should_return_error_when_species_not_found(update_tool, tool_context):
    result = await update_tool(bonsai_id=1, bonsai_name="Naruto", species_name="Unknown", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_not_found"}, \
        "Unknown species name should return species_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, update_bonsai_func, get_species_by_name_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_id, bonsai_name, bonsai_data):
        captured_calls.append((bonsai_id, bonsai_name, bonsai_data))
        return "confirmation text"

    tool = create_confirm_update_bonsai_tool(update_bonsai_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(bonsai_id=1, bonsai_name="Naruto", name="Goku", tool_context=tool_context)

    assert captured_calls == [(1, "Naruto", {"name": "Goku"})], \
        "build_confirmation_message should be called with bonsai_id, bonsai_name, and resolved bonsai_data"


@pytest.mark.asyncio
async def should_call_update_with_correct_bonsai_id_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(bonsai_id=1, bonsai_name="Naruto", name="Goku", tool_context=tool_context)

    assert captured_update["bonsai_id"] == 1, \
        "update_bonsai_func should receive the correct bonsai_id"


@pytest.mark.asyncio
async def should_call_update_with_new_name_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(bonsai_id=1, bonsai_name="Naruto", name="Goku", tool_context=tool_context)

    assert captured_update["bonsai_data"]["name"] == "Goku", \
        "update_bonsai_func should receive the new name in bonsai_data"


@pytest.mark.asyncio
async def should_resolve_species_id_when_user_confirms(update_tool, tool_context, captured_update):
    await update_tool(bonsai_id=1, bonsai_name="Naruto", species_name="Elm", tool_context=tool_context)

    assert captured_update["bonsai_data"]["species_id"] == 1, \
        "update_bonsai_func should receive the species_id resolved from species_name"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(update_tool, tool_context):
    result = await update_tool(bonsai_id=1, bonsai_name="Naruto", name="Goku", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_update_when_user_cancels(tool_context, update_bonsai_func, get_species_by_name_func, captured_update, build_confirmation_message):
    tool = create_confirm_update_bonsai_tool(update_bonsai_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(bonsai_id=1, bonsai_name="Naruto", name="Goku", tool_context=tool_context)

    assert captured_update == {}, \
        "update_bonsai_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, update_bonsai_func, get_species_by_name_func, build_confirmation_message):
    tool = create_confirm_update_bonsai_tool(update_bonsai_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(bonsai_id=1, bonsai_name="Naruto", name="Goku", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_bonsai_func(captured_update):
    def update_bonsai(bonsai_id: int, bonsai_data: dict) -> None:
        captured_update["bonsai_id"] = bonsai_id
        captured_update["bonsai_data"] = bonsai_data

    return update_bonsai


@pytest.fixture
def existing_species():
    return Species(id=1, name="Elm", scientific_name="Ulmus", care_guide={})


@pytest.fixture
def get_species_by_name_func(existing_species):
    def get_species_by_name(name: str) -> Species | None:
        return existing_species if name == existing_species.name else None

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
    def build(bonsai_id, bonsai_name, bonsai_data):
        return f"Confirm update bonsai '{bonsai_name}' (id={bonsai_id}): {bonsai_data}"

    return build


@pytest.fixture
def update_tool(update_bonsai_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_update_bonsai_tool(update_bonsai_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
