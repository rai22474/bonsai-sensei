import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_delete_phytosanitary_tool import (
    create_confirm_delete_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(delete_tool):
    result = delete_tool(name="Neem Oil", summary="Delete Neem Oil", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(delete_tool):
    result = delete_tool(
        name="Neem Oil",
        summary="Delete Neem Oil",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_name_is_missing(delete_tool, tool_context):
    result = delete_tool(name="", summary="Delete product", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Missing name should return a phytosanitary_name_required error",
    )


def should_return_confirmation_summary_when_delete_is_valid(delete_tool, tool_context):
    result = delete_tool(name="Neem Oil", summary="Delete Neem Oil", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"confirmation": "Delete Neem Oil"}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(delete_tool, tool_context, confirmation_store):
    delete_tool(name="Neem Oil", summary="Delete Neem Oil", tool_context=tool_context)

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
        equal_to("Delete Neem Oil"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_delete_with_correct_name(executed_delete):
    assert_that(
        executed_delete["name"],
        equal_to("Neem Oil"),
        "Executor should pass the correct name to delete_phytosanitary_func",
    )


def should_store_both_confirmations_when_deleted_twice(
    delete_tool, tool_context, confirmation_store
):
    delete_tool(name="Neem Oil", summary="First delete", tool_context=tool_context)
    delete_tool(name="Copper Sulfate", summary="Second delete", tool_context=tool_context)

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
def delete_phytosanitary_func(captured_delete):
    def delete_phytosanitary(name: str) -> None:
        captured_delete["name"] = name

    return delete_phytosanitary


@pytest.fixture
def delete_tool(delete_phytosanitary_func, confirmation_store):
    return create_confirm_delete_phytosanitary_tool(delete_phytosanitary_func, confirmation_store)


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(delete_tool, tool_context, confirmation_store):
    delete_tool(name="Neem Oil", summary="Delete Neem Oil", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_delete(delete_tool, tool_context, confirmation_store, captured_delete):
    delete_tool(name="Neem Oil", summary="Delete Neem Oil", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_delete
