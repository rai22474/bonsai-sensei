import pytest

from bonsai_sensei.domain.services.cultivation.species.confirm_create_species_tool import (
    create_confirm_create_species_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_species_name_is_missing(confirm_tool, tool_context):
    result = await confirm_tool(common_name="", summary="Create species", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_name_required"}, \
        "Missing common_name should return a species_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_species_already_exists(confirm_tool_with_existing, tool_context):
    result = await confirm_tool_with_existing(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_already_exists"}, \
        "Existing species should return a species_already_exists error"


@pytest.mark.asyncio
async def should_return_error_when_scientific_name_not_found(confirm_tool_no_results, tool_context):
    result = await confirm_tool_no_results(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert result == {"status": "error", "message": "scientific_name_not_found"}, \
        "No scientific name results should return a scientific_name_not_found error"


@pytest.mark.asyncio
async def should_create_species_with_correct_common_name_when_user_confirms(confirm_tool, tool_context, captured_species):
    await confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert captured_species[0].name == "Elm", \
        "Created species should use the common name"


@pytest.mark.asyncio
async def should_create_species_with_scientific_name_from_resolver_when_user_confirms(confirm_tool, tool_context, captured_species):
    await confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert captured_species[0].scientific_name == "Ulmus minor", \
        "Created species should use the scientific name returned by the resolver"


@pytest.mark.asyncio
async def should_create_species_with_care_guide_from_builder_when_user_confirms(confirm_tool, tool_context, captured_species):
    await confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert captured_species[0].care_guide["summary"] == "Water regularly and place in full sun.", \
        "Created species should use the care guide returned by the builder"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(confirm_tool, tool_context):
    result = await confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_species_when_user_cancels(tool_context, captured_species, create_species_func, get_species_by_name_func, scientific_name_resolver, care_guide_builder):
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, care_guide_builder, ask_confirmation_cancel)
    await tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert captured_species == [], \
        "create_species_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, create_species_func, get_species_by_name_func, scientific_name_resolver, care_guide_builder):
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, care_guide_builder, ask_confirmation_cancel)
    result = await tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


@pytest.fixture
def captured_species():
    return []


@pytest.fixture
def create_species_func(captured_species):
    def create_species(species: Species) -> Species:
        captured_species.append(species)
        return species

    return create_species


@pytest.fixture
def get_species_by_name_func():
    def get_species_by_name(name: str) -> Species | None:
        return None

    return get_species_by_name


@pytest.fixture
def existing_species_func():
    def get_species_by_name(name: str) -> Species | None:
        return Species(name=name, scientific_name="Ulmus minor", care_guide={})

    return get_species_by_name


@pytest.fixture
def scientific_name_resolver():
    def resolve(common_name: str) -> dict:
        return {"common_name": common_name, "scientific_names": ["Ulmus minor"]}

    return resolve


@pytest.fixture
def scientific_name_resolver_no_results():
    def resolve(common_name: str) -> dict:
        return {"common_name": common_name, "scientific_names": []}

    return resolve


@pytest.fixture
def care_guide_builder():
    def build(common_name: str, scientific_name: str) -> dict:
        return {
            "common_name": common_name,
            "scientific_name": scientific_name,
            "summary": "Water regularly and place in full sun.",
            "watering": None,
            "light": None,
            "soil": None,
            "pruning": None,
            "pests": None,
            "sources": [],
        }

    return build


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def ask_confirmation_confirm():
    async def ask_confirmation(question, tool_context=None):
        return True

    return ask_confirmation


@pytest.fixture
def confirm_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, care_guide_builder, ask_confirmation_confirm):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=get_species_by_name_func,
        scientific_name_resolver=scientific_name_resolver,
        care_guide_builder=care_guide_builder,
        ask_confirmation=ask_confirmation_confirm,
    )


@pytest.fixture
def confirm_tool_with_existing(create_species_func, existing_species_func, scientific_name_resolver, care_guide_builder, ask_confirmation_confirm):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=existing_species_func,
        scientific_name_resolver=scientific_name_resolver,
        care_guide_builder=care_guide_builder,
        ask_confirmation=ask_confirmation_confirm,
    )


@pytest.fixture
def confirm_tool_no_results(create_species_func, get_species_by_name_func, scientific_name_resolver_no_results, care_guide_builder, ask_confirmation_confirm):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=get_species_by_name_func,
        scientific_name_resolver=scientific_name_resolver_no_results,
        care_guide_builder=care_guide_builder,
        ask_confirmation=ask_confirmation_confirm,
    )
