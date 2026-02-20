import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_create_fertilizer_tool import (
    create_confirm_create_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(create_tool):
    result = create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(create_tool):
    result = create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_name_is_missing(create_tool, tool_context):
    result = create_tool(
        name="",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create fertilizer",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_name_required"}),
        "Missing name should return a fertilizer_name_required error",
    )


def should_return_error_when_usage_sheet_is_missing(create_tool, tool_context):
    result = create_tool(
        name="GreenBoom",
        usage_sheet="",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "usage_sheet_required"}),
        "Missing usage_sheet should return a usage_sheet_required error",
    )


def should_return_error_when_recommended_amount_is_missing(create_tool, tool_context):
    result = create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="",
        summary="Create GreenBoom",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "recommended_amount_required"}),
        "Missing recommended_amount should return a recommended_amount_required error",
    )


def should_return_confirmation_summary_when_create_is_valid(create_tool, tool_context):
    result = create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"confirmation": "Create GreenBoom"}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(create_tool, tool_context, confirmation_store):
    create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
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
        equal_to("Create GreenBoom"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_create_with_correct_name(executed_create):
    assert_that(
        executed_create["fertilizer"].name,
        equal_to("GreenBoom"),
        "Executor should pass the correct name to create_fertilizer_func",
    )


def should_execute_create_with_correct_usage_sheet(executed_create):
    assert_that(
        executed_create["fertilizer"].usage_sheet,
        equal_to("Apply once a month"),
        "Executor should pass the correct usage_sheet to create_fertilizer_func",
    )


def should_store_both_confirmations_when_created_twice(
    create_tool, tool_context, confirmation_store
):
    create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="First create",
        tool_context=tool_context,
    )
    create_tool(
        name="BlueForce",
        usage_sheet="Apply twice a month",
        recommended_amount="10 ml/L",
        summary="Second create",
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
def captured_create():
    return {}


@pytest.fixture
def create_fertilizer_func(captured_create):
    def create_fertilizer(fertilizer) -> None:
        captured_create["fertilizer"] = fertilizer

    return create_fertilizer


@pytest.fixture
def create_tool(create_fertilizer_func, confirmation_store):
    return create_confirm_create_fertilizer_tool(create_fertilizer_func, confirmation_store)


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(create_tool, tool_context, confirmation_store):
    create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
        tool_context=tool_context,
    )
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_create(create_tool, tool_context, confirmation_store, captured_create):
    create_tool(
        name="GreenBoom",
        usage_sheet="Apply once a month",
        recommended_amount="5 ml/L",
        summary="Create GreenBoom",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_create
