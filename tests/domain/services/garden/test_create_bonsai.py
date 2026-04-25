import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.services.garden.create_bonsai import (
    create_create_bonsai_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(create_tool, tool_context):
    result = await create_tool(name="", species_name="Elm", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai name should return bonsai_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_species_name_is_empty(create_tool, tool_context):
    result = await create_tool(name="Naruto", species_name="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "species_name_required"}),
        "Empty species name should return species_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_species_not_found(create_tool, tool_context):
    result = await create_tool(name="Naruto", species_name="Unknown", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "species_not_found"}),
        "Unknown species name should return species_not_found error")


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, create_bonsai_func, get_species_by_name_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(name, species_name):
        captured_calls.append((name, species_name))
        return "confirmation text"

    tool = create_create_bonsai_tool(create_bonsai_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(name="Naruto", species_name="Elm", tool_context=tool_context)

    assert_that(captured_calls, equal_to([("Naruto", "Elm")]),
        "build_confirmation_message should be called with name and species_name")


@pytest.mark.asyncio
async def should_create_bonsai_with_resolved_species_id_when_user_confirms(create_tool, tool_context, captured_bonsais):
    await create_tool(name="Naruto", species_name="Elm", tool_context=tool_context)

    assert_that(captured_bonsais[0].species_id, equal_to(1),
        "Bonsai should be created with the species_id resolved from species_name")


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(create_tool, tool_context):
    result = await create_tool(name="Naruto", species_name="Elm", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_create_bonsai_when_user_cancels(tool_context, create_bonsai_func, get_species_by_name_func, captured_bonsais, build_confirmation_message):
    tool = create_create_bonsai_tool(create_bonsai_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(name="Naruto", species_name="Elm", tool_context=tool_context)

    assert_that(captured_bonsais, equal_to([]),
        "create_bonsai_func should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, create_bonsai_func, get_species_by_name_func, build_confirmation_message):
    tool = create_create_bonsai_tool(create_bonsai_func, get_species_by_name_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(name="Naruto", species_name="Elm", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_bonsais():
    return []


@pytest.fixture
def create_bonsai_func(captured_bonsais):
    def create_bonsai(bonsai: Bonsai) -> Bonsai:
        captured_bonsais.append(bonsai)
        return bonsai

    return create_bonsai


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
    def build(name, species_name):
        return f"Confirm create bonsai '{name}' ({species_name})"

    return build


@pytest.fixture
def create_tool(create_bonsai_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message):
    return create_create_bonsai_tool(create_bonsai_func, get_species_by_name_func, ask_confirmation_confirm, build_confirmation_message)
