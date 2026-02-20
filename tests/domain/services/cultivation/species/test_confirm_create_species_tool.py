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


def should_return_error_when_tool_context_is_none(confirm_tool, new_species):
    result = confirm_tool(**new_species, tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(confirm_tool, new_species):
    result = confirm_tool(**new_species, tool_context=MockToolContext(user_id=None))

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_scientific_name_is_none(confirm_tool, tool_context):
    result = confirm_tool(
        common_name="Elm",
        scientific_name=None,
        summary="Summary",
        sources=[],
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "scientific_name_required"}),
        "None scientific name should return a scientific_name_required error",
    )


def should_return_error_when_scientific_name_is_whitespace(confirm_tool, tool_context):
    result = confirm_tool(
        common_name="Elm",
        scientific_name="   ",
        summary="Summary",
        sources=[],
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "scientific_name_required"}),
        "Whitespace-only scientific name should return a scientific_name_required error",
    )


def should_return_confirmation_summary_when_all_data_is_valid(
    confirm_tool, tool_context, new_species
):
    result = confirm_tool(**new_species, tool_context=tool_context)

    assert_that(
        result,
        equal_to({"confirmation": new_species["summary"]}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    confirm_tool, tool_context, confirmation_store, new_species
):
    confirm_tool(**new_species, tool_context=tool_context)

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


def should_store_confirmation_with_correct_summary(pending_confirmation, new_species):
    assert_that(
        pending_confirmation.summary,
        equal_to(new_species["summary"]),
        "Stored confirmation summary should match the argument",
    )


def should_create_species_with_common_name_on_execute(executed_species):
    assert_that(
        executed_species.name,
        equal_to("Elm"),
        "Created species should use the common name",
    )


def should_create_species_with_normalized_scientific_name_on_execute(executed_species):
    assert_that(
        executed_species.scientific_name,
        equal_to("Ulmus minor"),
        "Scientific name should be normalized (trimmed) when creating the species",
    )


def should_include_watering_in_care_guide_on_execute(executed_species):
    assert_that(
        executed_species.care_guide["watering"],
        equal_to("Moderate watering"),
        "care_guide should include the watering field",
    )


def should_include_sources_in_care_guide_on_execute(executed_species):
    assert_that(
        executed_species.care_guide["sources"],
        equal_to(["https://example.com"]),
        "care_guide should include the provided sources",
    )


def should_store_both_confirmations_when_created_twice(
    confirm_tool, tool_context, confirmation_store
):
    confirm_tool(
        common_name="Elm",
        scientific_name="Ulmus minor",
        summary="First confirmation",
        sources=[],
        tool_context=tool_context,
    )
    confirm_tool(
        common_name="Pine",
        scientific_name="Pinus thunbergii",
        summary="Second confirmation",
        sources=[],
        tool_context=tool_context,
    )

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Both confirmations should be stored independently for the same user",
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
def confirm_tool(create_species_func, confirmation_store):
    return create_confirm_create_species_tool(create_species_func, confirmation_store)


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def new_species():
    return {
        "common_name": "Elm",
        "scientific_name": "Ulmus minor",
        "summary": "The elm is a resilient species.",
        "sources": ["https://example.com/elm"],
        "watering": "Moderate watering",
        "light": "Direct light",
        "soil": "Well-drained soil",
        "pruning": "Prune in spring",
        "pests": "Aphids",
    }


@pytest.fixture
def pending_confirmation(confirm_tool, tool_context, confirmation_store, new_species):
    confirm_tool(**new_species, tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_species(confirm_tool, tool_context, confirmation_store, captured_species):
    confirm_tool(
        common_name="Elm",
        scientific_name="  Ulmus minor  ",
        summary="Summary",
        sources=["https://example.com"],
        watering="Moderate watering",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_species[0]
