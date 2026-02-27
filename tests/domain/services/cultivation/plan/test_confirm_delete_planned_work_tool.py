import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.confirm_delete_planned_work_tool import (
    create_confirm_delete_planned_work_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(delete_tool):
    result = delete_tool(planned_work_id=1, summary="Remove planned fertilization", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(delete_tool):
    result = delete_tool(
        planned_work_id=1,
        summary="Remove planned fertilization",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_planned_work_not_found(delete_tool, tool_context):
    result = delete_tool(planned_work_id=999, summary="Remove work", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"status": "error", "message": "planned_work_not_found"}),
        "Non-existent work_id should return a not_found error",
    )


def should_return_confirmation_pending_when_work_exists(delete_tool, tool_context):
    result = delete_tool(planned_work_id=1, summary="Remove planned fertilization", tool_context=tool_context)

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Remove planned fertilization",
        }),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(delete_tool, tool_context, confirmation_store):
    delete_tool(planned_work_id=1, summary="Remove planned fertilization", tool_context=tool_context)

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


def should_execute_delete_with_correct_work_id(executed_delete):
    assert_that(
        executed_delete["work_id"],
        equal_to(1),
        "Executor should pass the correct work_id to delete_planned_work_func",
    )


def should_deduplicate_second_delete_for_same_work_id(delete_tool, tool_context, confirmation_store):
    delete_tool(planned_work_id=1, summary="First delete", tool_context=tool_context)
    delete_tool(planned_work_id=1, summary="Second delete", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(1),
        "Second delete for the same work_id should be deduplicated, leaving only one confirmation",
    )


def should_store_both_deletes_for_different_work_ids(delete_tool, tool_context, confirmation_store):
    delete_tool(planned_work_id=1, summary="First delete", tool_context=tool_context)
    delete_tool(planned_work_id=2, summary="Second delete", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Deletes for different work_ids should each be stored as independent confirmations",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


@pytest.fixture
def captured_delete():
    return {}


@pytest.fixture
def planned_work_stub():
    work = PlannedWork(bonsai_id=10, work_type="fertilizer_application", payload={}, scheduled_date="2026-03-15")
    work.id = 1
    return work


@pytest.fixture
def get_planned_work_func(planned_work_stub):
    def get_planned_work(work_id: int):
        return None if work_id == 999 else planned_work_stub
    return get_planned_work


@pytest.fixture
def delete_planned_work_func(captured_delete):
    def delete_planned_work(work_id: int) -> None:
        captured_delete["work_id"] = work_id
    return delete_planned_work


@pytest.fixture
def delete_tool(get_planned_work_func, delete_planned_work_func, confirmation_store):
    return create_confirm_delete_planned_work_tool(
        get_planned_work_func=get_planned_work_func,
        delete_planned_work_func=delete_planned_work_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(delete_tool, tool_context, confirmation_store):
    delete_tool(planned_work_id=1, summary="Remove planned fertilization", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_delete(delete_tool, tool_context, confirmation_store, captured_delete):
    delete_tool(planned_work_id=1, summary="Remove planned fertilization", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_delete
