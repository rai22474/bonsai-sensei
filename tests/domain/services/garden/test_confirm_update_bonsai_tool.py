import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.garden.confirm_update_bonsai_tool import (
    create_confirm_update_bonsai_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(update_tool):
    result = update_tool(
        bonsai_id=1, summary="Update bonsai", tool_context=None, name="New name"
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(update_tool):
    result = update_tool(
        bonsai_id=1,
        summary="Update bonsai",
        tool_context=MockToolContext(user_id=None),
        name="New name",
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_bonsai_id_is_missing(update_tool, tool_context):
    result = update_tool(
        bonsai_id=0, summary="Update bonsai", tool_context=tool_context, name="New name"
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_id_required"}),
        "Missing bonsai_id should return a bonsai_id_required error",
    )


def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = update_tool(
        bonsai_id=1, summary="Update bonsai", tool_context=tool_context
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_update_required"}),
        "No update fields should return a bonsai_update_required error",
    )


def should_return_error_when_species_not_found(update_tool, tool_context):
    result = update_tool(
        bonsai_id=1,
        summary="Update bonsai",
        species_name="Unknown",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_not_found"}),
        "An unknown species name should return a species_not_found error",
    )


def should_return_confirmation_summary_when_update_is_valid(update_tool, tool_context):
    result = update_tool(
        bonsai_id=1,
        summary="Rename bonsai",
        name="Goku",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"confirmation": "Rename bonsai"}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    update_tool, tool_context, confirmation_store
):
    update_tool(
        bonsai_id=1, summary="Rename bonsai", name="Goku", tool_context=tool_context
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
        equal_to("Rename bonsai"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_update_with_correct_bonsai_id(executed_update):
    assert_that(
        executed_update["bonsai_id"],
        equal_to(1),
        "Executor should pass the bonsai_id to update_bonsai_func",
    )


def should_execute_update_with_new_name_in_bonsai_data(executed_update):
    assert_that(
        executed_update["bonsai_data"]["name"],
        equal_to("Goku"),
        "Executor should include the new name in bonsai_data",
    )


def should_execute_update_with_species_id_resolved_from_name(
    update_tool, tool_context, confirmation_store, captured_update
):
    update_tool(
        bonsai_id=1,
        summary="Change species",
        species_name="Elm",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    assert_that(
        captured_update["bonsai_data"]["species_id"],
        equal_to(1),
        "Executor should resolve species_id from the species name",
    )


def should_store_both_confirmations_when_updated_twice(
    update_tool, tool_context, confirmation_store
):
    update_tool(
        bonsai_id=1, summary="First update", name="Goku", tool_context=tool_context
    )
    update_tool(
        bonsai_id=1, summary="Second update", name="Vegeta", tool_context=tool_context
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
def update_tool(update_bonsai_func, get_species_by_name_func, confirmation_store):
    return create_confirm_update_bonsai_tool(
        update_bonsai_func, get_species_by_name_func, confirmation_store
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(update_tool, tool_context, confirmation_store):
    update_tool(
        bonsai_id=1,
        summary="Rename bonsai",
        name="Goku",
        tool_context=tool_context,
    )
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_update(update_tool, tool_context, confirmation_store, captured_update):
    update_tool(
        bonsai_id=1,
        summary="Rename bonsai",
        name="Goku",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_update
