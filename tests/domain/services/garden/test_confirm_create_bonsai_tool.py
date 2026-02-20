import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.garden.confirm_create_bonsai_tool import (
    create_confirm_create_bonsai_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(create_tool):
    result = create_tool(
        name="Naruto", species_name="Elm", summary="Create Naruto", tool_context=None
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(create_tool):
    result = create_tool(
        name="Naruto",
        species_name="Elm",
        summary="Create Naruto",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_bonsai_name_is_empty(create_tool, tool_context):
    result = create_tool(
        name="", species_name="Elm", summary="Create bonsai", tool_context=tool_context
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai name should return a bonsai_name_required error",
    )


def should_return_error_when_species_name_is_empty(create_tool, tool_context):
    result = create_tool(
        name="Naruto",
        species_name="",
        summary="Create bonsai",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_name_required"}),
        "Empty species name should return a species_name_required error",
    )


def should_return_error_when_species_not_found(create_tool, tool_context):
    result = create_tool(
        name="Naruto",
        species_name="Unknown",
        summary="Create bonsai",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_not_found"}),
        "A species name with no match should return a species_not_found error",
    )


def should_return_confirmation_summary_when_create_is_valid(create_tool, tool_context):
    result = create_tool(
        name="Naruto",
        species_name="Elm",
        summary="Create Naruto bonsai",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"confirmation": "Create Naruto bonsai"}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    create_tool, tool_context, confirmation_store
):
    create_tool(
        name="Naruto",
        species_name="Elm",
        summary="Create Naruto bonsai",
        tool_context=tool_context,
    )

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
        equal_to("Create Naruto bonsai"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_create_with_correct_bonsai_name(executed_bonsai):
    assert_that(
        executed_bonsai.name,
        equal_to("Naruto"),
        "Executor should create a bonsai with the given name",
    )


def should_execute_create_with_species_id_resolved_from_name(executed_bonsai):
    assert_that(
        executed_bonsai.species_id,
        equal_to(1),
        "Executor should resolve the species id from the species name",
    )


def should_store_both_confirmations_when_created_twice(
    create_tool, tool_context, confirmation_store
):
    create_tool(
        name="Naruto",
        species_name="Elm",
        summary="First bonsai",
        tool_context=tool_context,
    )
    create_tool(
        name="Goku",
        species_name="Elm",
        summary="Second bonsai",
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
def captured_bonsai():
    return []


@pytest.fixture
def create_bonsai_func(captured_bonsai):
    def create_bonsai(bonsai: Bonsai) -> Bonsai:
        captured_bonsai.append(bonsai)
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
def create_tool(create_bonsai_func, get_species_by_name_func, confirmation_store):
    return create_confirm_create_bonsai_tool(
        create_bonsai_func, get_species_by_name_func, confirmation_store
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(create_tool, tool_context, confirmation_store):
    create_tool(
        name="Naruto",
        species_name="Elm",
        summary="Create Naruto bonsai",
        tool_context=tool_context,
    )
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_bonsai(create_tool, tool_context, confirmation_store, captured_bonsai):
    create_tool(
        name="Naruto",
        species_name="Elm",
        summary="Create Naruto bonsai",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_bonsai[0]
