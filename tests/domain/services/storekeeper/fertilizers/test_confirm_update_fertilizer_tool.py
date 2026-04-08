import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_update_fertilizer_tool import (
    create_confirm_update_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(update_tool):
    result = update_tool(
        name="GreenBoom",
        summary="Update GreenBoom",
        usage_sheet="New sheet",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(update_tool):
    result = update_tool(
        name="GreenBoom",
        summary="Update GreenBoom",
        usage_sheet="New sheet",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_name_is_missing(update_tool, tool_context):
    result = update_tool(
        name="",
        summary="Update fertilizer",
        usage_sheet="New sheet",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_name_required"}),
        "Missing name should return a fertilizer_name_required error",
    )


def should_return_error_when_fertilizer_not_found(update_tool_not_found, tool_context):
    result = update_tool_not_found(
        name="GreenBoom",
        summary="Update GreenBoom",
        usage_sheet="New sheet",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_not_found"}),
        "Non-existent fertilizer should return a fertilizer_not_found error",
    )


def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = update_tool(
        name="GreenBoom",
        summary="Update GreenBoom",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_update_required"}),
        "No update fields should return a fertilizer_update_required error",
    )


def should_return_confirmation_summary_when_update_is_valid(update_tool, tool_context):
    result = update_tool(
        name="GreenBoom",
        summary="Update GreenBoom",
        usage_sheet="New sheet",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Update GreenBoom",
        }),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(update_tool, tool_context, confirmation_store):
    update_tool(
        name="GreenBoom",
        summary="Update GreenBoom",
        usage_sheet="New sheet",
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
        equal_to("Update GreenBoom"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_update_with_correct_name(executed_update):
    assert_that(
        executed_update["name"],
        equal_to("GreenBoom"),
        "Executor should pass the correct name to update_fertilizer_func",
    )


def should_execute_update_with_correct_usage_sheet(executed_update):
    assert_that(
        executed_update["fertilizer_data"]["usage_sheet"],
        equal_to("New sheet"),
        "Executor should include the new usage_sheet in fertilizer_data",
    )


def should_deduplicate_second_update_for_same_fertilizer(
    update_tool, tool_context, confirmation_store
):
    update_tool(name="GreenBoom", summary="First update", usage_sheet="Sheet 1", tool_context=tool_context)
    update_tool(name="GreenBoom", summary="Second update", recommended_amount="10 ml/L", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(1),
        "Second update for the same fertilizer should be deduplicated, leaving only one confirmation",
    )


def should_store_both_updates_for_different_fertilizers(
    update_tool, tool_context, confirmation_store
):
    update_tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="Sheet 1", tool_context=tool_context)
    update_tool(name="BlueForce", summary="Update BlueForce", usage_sheet="Sheet 2", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Updates for different fertilizers should each be stored as independent confirmations",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_fertilizer_func(captured_update):
    def update_fertilizer(name: str, fertilizer_data: dict) -> None:
        captured_update["name"] = name
        captured_update["fertilizer_data"] = fertilizer_data

    return update_fertilizer


@pytest.fixture
def get_fertilizer_by_name_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return Fertilizer(name=name, usage_sheet="Sheet", recommended_amount="5 ml/L")

    return get_fertilizer_by_name


@pytest.fixture
def get_fertilizer_by_name_not_found():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return None

    return get_fertilizer_by_name


@pytest.fixture
def update_tool(update_fertilizer_func, get_fertilizer_by_name_func, confirmation_store):
    return create_confirm_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def update_tool_not_found(update_fertilizer_func, get_fertilizer_by_name_not_found, confirmation_store):
    return create_confirm_update_fertilizer_tool(
        update_fertilizer_func=update_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_not_found,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(update_tool, tool_context, confirmation_store):
    update_tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_update(update_tool, tool_context, confirmation_store, captured_update):
    update_tool(name="GreenBoom", summary="Update GreenBoom", usage_sheet="New sheet", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_update
