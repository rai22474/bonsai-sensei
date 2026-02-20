import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.cultivation.species.confirm_delete_species_tool import (
    create_confirm_delete_species_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(delete_tool):
    result = delete_tool(species_name="Elm", summary="Delete Elm", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(delete_tool):
    result = delete_tool(
        species_name="Elm",
        summary="Delete Elm",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_species_name_is_empty(delete_tool, tool_context):
    result = delete_tool(
        species_name="",
        summary="Delete species",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_name_required"}),
        "Empty species name should return a species_name_required error",
    )


def should_return_error_when_species_not_found(delete_tool, tool_context):
    result = delete_tool(
        species_name="Unknown",
        summary="Delete species",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_not_found"}),
        "A name that does not match any species should return a species_not_found error",
    )


def should_return_confirmation_summary_when_delete_is_valid(
    delete_tool, tool_context
):
    result = delete_tool(
        species_name="Elm",
        summary="Delete Elm",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"confirmation": "Delete Elm"}),
        "Valid delete input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    delete_tool, tool_context, confirmation_store
):
    delete_tool(species_name="Elm", summary="Delete Elm", tool_context=tool_context)

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
        equal_to("Delete Elm"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_delete_with_correct_species_id(executed_delete):
    assert_that(
        executed_delete["species_id"],
        equal_to(1),
        "Executor should pass the existing species id to delete_species_func",
    )


def should_store_both_confirmations_when_deleted_twice(
    delete_tool, tool_context, confirmation_store
):
    delete_tool(species_name="Elm", summary="First delete", tool_context=tool_context)
    delete_tool(species_name="Elm", summary="Second delete", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Both confirmations should be stored independently for the same user",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


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
    return Species(id=1, name="Elm", scientific_name="Ulmus", care_guide={})


@pytest.fixture
def get_species_by_name_func(existing_species):
    def get_species_by_name(name: str) -> Species | None:
        return existing_species if name == existing_species.name else None

    return get_species_by_name


@pytest.fixture
def delete_tool(delete_species_func, get_species_by_name_func, confirmation_store):
    return create_confirm_delete_species_tool(
        delete_species_func, get_species_by_name_func, confirmation_store
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(delete_tool, tool_context, confirmation_store):
    delete_tool(species_name="Elm", summary="Delete Elm", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_delete(delete_tool, tool_context, confirmation_store, captured_delete):
    delete_tool(species_name="Elm", summary="Delete Elm", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_delete
