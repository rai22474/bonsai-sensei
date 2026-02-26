from datetime import date

import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.garden.confirm_execute_planned_work_tool import (
    create_confirm_execute_planned_work_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(execute_planned_work_tool):
    result = execute_planned_work_tool(
        work_id=1,
        summary="Execute planned work",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_work_id_is_zero(execute_planned_work_tool, tool_context):
    result = execute_planned_work_tool(
        work_id=0,
        summary="Execute planned work",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "work_id_required"}),
        "Zero work_id should return a work_id_required error",
    )


def should_return_error_when_planned_work_not_found(execute_planned_work_tool, tool_context):
    result = execute_planned_work_tool(
        work_id=999,
        summary="Execute planned work",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "planned_work_not_found"}),
        "Unknown work_id should return a planned_work_not_found error",
    )


def should_return_confirmation_pending_when_valid(execute_planned_work_tool, tool_context):
    result = execute_planned_work_tool(
        work_id=1,
        summary="Execute BioGrow fertilization for Kaze",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Execute BioGrow fertilization for Kaze",
        }),
        "Valid input should return a confirmation_pending dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    execute_planned_work_tool, tool_context, confirmation_store
):
    execute_planned_work_tool(
        work_id=1,
        summary="Execute BioGrow fertilization for Kaze",
        tool_context=tool_context,
    )

    assert_that(
        confirmation_store.get_pending("user-123"),
        not_none(),
        "Pending confirmation should be stored in the store",
    )


def should_record_event_with_correct_type_on_execution(
    execute_planned_work_tool, tool_context, confirmation_store, captured_events
):
    execute_planned_work_tool(
        work_id=1,
        summary="Execute BioGrow fertilization for Kaze",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    assert_that(
        captured_events[0].event_type,
        equal_to("fertilizer_application"),
        "Executed confirmation should record a fertilizer_application event",
    )


def should_delete_planned_work_on_execution(
    execute_planned_work_tool, tool_context, confirmation_store, deleted_work_ids
):
    execute_planned_work_tool(
        work_id=1,
        summary="Execute BioGrow fertilization for Kaze",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    assert_that(
        deleted_work_ids,
        equal_to([1]),
        "Executed confirmation should delete the planned work",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


@pytest.fixture
def captured_events():
    return []


@pytest.fixture
def deleted_work_ids():
    return []


@pytest.fixture
def record_bonsai_event_func(captured_events):
    def record_bonsai_event(bonsai_event: BonsaiEvent) -> BonsaiEvent:
        captured_events.append(bonsai_event)
        return bonsai_event

    return record_bonsai_event


@pytest.fixture
def delete_planned_work_func(deleted_work_ids):
    def delete_planned_work(work_id: int) -> bool:
        deleted_work_ids.append(work_id)
        return True

    return delete_planned_work


@pytest.fixture
def existing_planned_work():
    return PlannedWork(
        id=1,
        bonsai_id=10,
        work_type="fertilizer_application",
        payload={"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"},
        scheduled_date=date(2026, 3, 15),
    )


@pytest.fixture
def get_planned_work_func(existing_planned_work):
    def get_planned_work(work_id: int) -> PlannedWork | None:
        return existing_planned_work if work_id == existing_planned_work.id else None

    return get_planned_work


@pytest.fixture
def execute_planned_work_tool(
    get_planned_work_func,
    record_bonsai_event_func,
    delete_planned_work_func,
    confirmation_store,
):
    return create_confirm_execute_planned_work_tool(
        get_planned_work_func=get_planned_work_func,
        record_bonsai_event_func=record_bonsai_event_func,
        delete_planned_work_func=delete_planned_work_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")
