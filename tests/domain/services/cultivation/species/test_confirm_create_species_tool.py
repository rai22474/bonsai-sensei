import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
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
    result = await confirm_tool(common_name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_name_required"}, \
        "Missing common_name should return a species_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_species_already_exists(confirm_tool_with_existing, tool_context):
    result = await confirm_tool_with_existing(common_name="Elm", tool_context=tool_context)

    assert result == {"status": "error", "message": "species_already_exists"}, \
        "Existing species should return a species_already_exists error"


@pytest.mark.asyncio
async def should_return_error_when_scientific_name_not_found(confirm_tool_no_results, tool_context):
    result = await confirm_tool_no_results(common_name="Elm", tool_context=tool_context)

    assert result == {"status": "error", "message": "scientific_name_not_found"}, \
        "No scientific name results should return a scientific_name_not_found error"


@pytest.mark.asyncio
async def should_return_ambiguous_when_multiple_scientific_names_found(tool_context, create_species_func, get_species_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    scientific_name_resolver_multi = lambda name: {"common_name": name, "scientific_names": ["Juniperus chinensis", "Juniperus communis"]}
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver_multi, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message)
    result = await tool(common_name="Junípero", tool_context=tool_context)

    assert result == {"status": "ambiguous", "candidates": ["Juniperus chinensis", "Juniperus communis"]}, \
        "Tool should return ambiguous status with candidate list when multiple names are found"


@pytest.mark.asyncio
async def should_not_create_species_on_ambiguous_result(tool_context, create_species_func, get_species_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message, captured_species):
    scientific_name_resolver_multi = lambda name: {"common_name": name, "scientific_names": ["Juniperus chinensis", "Juniperus communis"]}
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver_multi, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message)
    await tool(common_name="Junípero", tool_context=tool_context)

    assert captured_species == [], \
        "create_species_func should not be called when the result is ambiguous"


@pytest.mark.asyncio
async def should_skip_resolver_and_use_provided_scientific_name(tool_context, create_species_func, get_species_by_name_func, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message, captured_species):
    scientific_name_resolver_multi = lambda name: {"common_name": name, "scientific_names": ["Juniperus chinensis", "Juniperus communis"]}
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver_multi, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message)
    await tool(common_name="Junípero", scientific_name="Juniperus chinensis", tool_context=tool_context)

    assert captured_species[0].scientific_name == "Juniperus chinensis", \
        "When scientific_name is provided directly, tool should use it without resolving"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(common_name, scientific_name):
        captured_calls.append((common_name, scientific_name))
        return "confirmation text"

    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message)
    await tool(common_name="Elm", tool_context=tool_context)

    assert len(captured_calls) == 1 and captured_calls[0] == ("Elm", "Ulmus minor"), \
        "build_confirmation_message should be called with common_name and resolved scientific_name"


@pytest.mark.asyncio
async def should_create_species_with_correct_common_name_when_user_confirms(confirm_tool, tool_context, captured_species):
    await confirm_tool(common_name="Elm", tool_context=tool_context)

    assert captured_species[0].name == "Elm", \
        "Created species should use the common name"


@pytest.mark.asyncio
async def should_create_species_with_scientific_name_from_resolver_when_user_confirms(confirm_tool, tool_context, captured_species):
    await confirm_tool(common_name="Elm", tool_context=tool_context)

    assert captured_species[0].scientific_name == "Ulmus minor", \
        "Created species should use the scientific name returned by the resolver"


@pytest.mark.asyncio
async def should_create_species_with_wiki_path_from_builder_when_user_confirms(confirm_tool, tool_context, captured_species):
    await confirm_tool(common_name="Elm", tool_context=tool_context)

    assert captured_species[0].wiki_path == "species/elm.md", \
        "Created species should use the wiki_path returned by the builder"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(confirm_tool, tool_context):
    result = await confirm_tool(common_name="Elm", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_species_when_user_cancels(tool_context, captured_species, create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, build_confirmation_message):
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, ask_confirmation_cancel, build_confirmation_message)
    await tool(common_name="Elm", tool_context=tool_context)

    assert captured_species == [], \
        "create_species_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, build_confirmation_message):
    tool = create_confirm_create_species_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(common_name="Elm", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


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
        return Species(name=name, scientific_name="Ulmus minor")

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
def wiki_page_builder():
    async def build(common_name: str, scientific_name: str) -> str:
        return f"species/{common_name.lower()}.md"

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
def build_confirmation_message():
    def build(common_name, scientific_name):
        return f"Confirm create species '{common_name}' ({scientific_name})"

    return build


@pytest.fixture
def confirm_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=get_species_by_name_func,
        scientific_name_resolver=scientific_name_resolver,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def confirm_tool_with_existing(create_species_func, existing_species_func, scientific_name_resolver, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=existing_species_func,
        scientific_name_resolver=scientific_name_resolver,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )


@pytest.fixture
def confirm_tool_no_results(create_species_func, get_species_by_name_func, scientific_name_resolver_no_results, wiki_page_builder, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=get_species_by_name_func,
        scientific_name_resolver=scientific_name_resolver_no_results,
        wiki_page_builder=wiki_page_builder,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
