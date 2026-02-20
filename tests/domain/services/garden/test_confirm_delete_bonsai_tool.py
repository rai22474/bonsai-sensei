import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.garden.confirm_delete_bonsai_tool import (
    create_confirm_delete_bonsai_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(delete_tool):
    result = delete_tool(bonsai_id=1, summary="Delete bonsai", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(delete_tool):
    result = delete_tool(
        bonsai_id=1,
        summary="Delete bonsai",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_bonsai_id_is_missing(delete_tool, tool_context):
    result = delete_tool(bonsai_id=0, summary="Delete bonsai", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_id_required"}),
        "Missing bonsai_id should return a bonsai_id_required error",
    )


def should_return_confirmation_summary_when_delete_is_valid(delete_tool, tool_context):
    result = delete_tool(bonsai_id=1, summary="Delete Naruto", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"confirmation": "Delete Naruto"}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    delete_tool, tool_context, confirmation_store
):
    delete_tool(bonsai_id=1, summary="Delete Naruto", tool_context=tool_context)

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
        equal_to("Delete Naruto"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_delete_with_correct_bonsai_id(executed_delete):
    assert_that(
        executed_delete["bonsai_id"],
        equal_to(1),
        "Executor should pass the bonsai_id to delete_bonsai_func",
    )


def should_store_both_confirmations_when_deleted_twice(
    delete_tool, tool_context, confirmation_store
):
    delete_tool(bonsai_id=1, summary="First delete", tool_context=tool_context)
    delete_tool(bonsai_id=2, summary="Second delete", tool_context=tool_context)

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
def delete_bonsai_func(captured_delete):
    def delete_bonsai(bonsai_id: int) -> None:
        captured_delete["bonsai_id"] = bonsai_id

    return delete_bonsai


@pytest.fixture
def delete_tool(delete_bonsai_func, confirmation_store):
    return create_confirm_delete_bonsai_tool(delete_bonsai_func, confirmation_store)


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(delete_tool, tool_context, confirmation_store):
    delete_tool(bonsai_id=1, summary="Delete Naruto", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_delete(delete_tool, tool_context, confirmation_store, captured_delete):
    delete_tool(bonsai_id=1, summary="Delete Naruto", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_delete
