import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.cultivation.species.confirm_create_species_tool import (
    create_confirm_create_species_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(confirm_tool):
    result = confirm_tool(common_name="Elm", summary="Create Elm", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(confirm_tool):
    result = confirm_tool(
        common_name="Elm",
        summary="Create Elm",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_species_name_is_missing(confirm_tool, tool_context):
    result = confirm_tool(common_name="", summary="Create species", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_name_required"}),
        "Missing common_name should return a species_name_required error",
    )


def should_return_error_when_species_already_exists(confirm_tool_with_existing, tool_context):
    result = confirm_tool_with_existing(
        common_name="Elm", summary="Create Elm", tool_context=tool_context
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_already_exists"}),
        "Existing species should return a species_already_exists error",
    )


def should_return_error_when_scientific_name_not_found(confirm_tool_no_results, tool_context):
    result = confirm_tool_no_results(
        common_name="Elm", summary="Create Elm", tool_context=tool_context
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "scientific_name_not_found"}),
        "No scientific name results should return a scientific_name_not_found error",
    )


def should_return_confirmation_summary_when_create_is_valid(confirm_tool, tool_context):
    result = confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Create Elm",
        }),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(confirm_tool, tool_context, confirmation_store):
    confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)

    assert_that(
        confirmation_store.get_pending("user-123"),
        not_none(),
        "Pending confirmation should be stored in the store",
    )


def should_store_confirmation_with_correct_user_id(pending_confirmation):
    assert_that(
        pending_confirmation.user_id,
        equal_to("user-123"),
        "Stored confirmation should carry the correct user_id",
    )


def should_store_confirmation_with_correct_summary(pending_confirmation):
    assert_that(
        pending_confirmation.summary,
        equal_to("Create Elm"),
        "Stored confirmation summary should match the argument",
    )


def should_create_species_with_correct_common_name(executed_species):
    assert_that(
        executed_species.name,
        equal_to("Elm"),
        "Created species should use the common name",
    )


def should_create_species_with_scientific_name_from_resolver(executed_species):
    assert_that(
        executed_species.scientific_name,
        equal_to("Ulmus minor"),
        "Created species should use the scientific name returned by the resolver",
    )


def should_create_species_with_care_guide_from_builder(executed_species):
    assert_that(
        executed_species.care_guide["summary"],
        equal_to("Water regularly and place in full sun."),
        "Created species should use the care guide returned by the builder",
    )


def should_deduplicate_second_create_for_same_species(
    confirm_tool, tool_context, confirmation_store
):
    confirm_tool(common_name="Elm", summary="First create", tool_context=tool_context)
    confirm_tool(common_name="Elm", summary="Second create", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(1),
        "Second create for the same species should be deduplicated, leaving only one confirmation",
    )


def should_store_both_creates_for_different_species(
    confirm_tool, tool_context, confirmation_store
):
    confirm_tool(common_name="Elm", summary="First create", tool_context=tool_context)
    confirm_tool(common_name="Pine", summary="Second create", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Creates for different species should each be stored as independent confirmations",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


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
def confirm_tool(create_species_func, get_species_by_name_func, scientific_name_resolver, care_guide_builder, confirmation_store):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=get_species_by_name_func,
        scientific_name_resolver=scientific_name_resolver,
        care_guide_builder=care_guide_builder,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def confirm_tool_with_existing(create_species_func, existing_species_func, scientific_name_resolver, care_guide_builder, confirmation_store):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=existing_species_func,
        scientific_name_resolver=scientific_name_resolver,
        care_guide_builder=care_guide_builder,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def confirm_tool_no_results(create_species_func, get_species_by_name_func, scientific_name_resolver_no_results, care_guide_builder, confirmation_store):
    return create_confirm_create_species_tool(
        create_species_func=create_species_func,
        get_species_by_name_func=get_species_by_name_func,
        scientific_name_resolver=scientific_name_resolver_no_results,
        care_guide_builder=care_guide_builder,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(confirm_tool, tool_context, confirmation_store):
    confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_species(confirm_tool, tool_context, confirmation_store, captured_species):
    confirm_tool(common_name="Elm", summary="Create Elm", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_species[0]
