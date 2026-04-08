import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_update_phytosanitary_tool import (
    create_confirm_update_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(update_tool):
    result = update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(update_tool):
    result = update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
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
        summary="Update product",
        usage_sheet="New instructions",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Missing name should return a phytosanitary_name_required error",
    )


def should_return_error_when_phytosanitary_not_found(update_tool_not_found, tool_context):
    result = update_tool_not_found(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_not_found"}),
        "Non-existent product should return a phytosanitary_not_found error",
    )


def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_update_required"}),
        "No update fields should return a phytosanitary_update_required error",
    )


def should_return_confirmation_summary_when_update_is_valid(update_tool, tool_context):
    result = update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Update Neem Oil",
        }),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(update_tool, tool_context, confirmation_store):
    update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
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
        equal_to("Update Neem Oil"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_update_with_correct_name(executed_update):
    assert_that(
        executed_update["name"],
        equal_to("Neem Oil"),
        "Executor should pass the correct name to update_phytosanitary_func",
    )


def should_execute_update_with_correct_usage_sheet(executed_update):
    assert_that(
        executed_update["phytosanitary_data"]["usage_sheet"],
        equal_to("New instructions"),
        "Executor should include the new usage_sheet in phytosanitary_data",
    )


def should_execute_update_with_correct_target(executed_update_with_target):
    assert_that(
        executed_update_with_target["phytosanitary_data"]["recommended_for"],
        equal_to("Aphids"),
        "Executor should include the new target as recommended_for in phytosanitary_data",
    )


def should_deduplicate_second_update_for_same_phytosanitary(
    update_tool, tool_context, confirmation_store
):
    update_tool(
        name="Neem Oil",
        summary="First update",
        usage_sheet="Sheet 1",
        tool_context=tool_context,
    )
    update_tool(
        name="Neem Oil",
        summary="Second update",
        target="Aphids",
        tool_context=tool_context,
    )

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(1),
        "Second update for the same phytosanitary product should be deduplicated, leaving only one confirmation",
    )


def should_store_both_updates_for_different_phytosanitary_products(
    update_tool, tool_context, confirmation_store
):
    update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="Sheet 1",
        tool_context=tool_context,
    )
    update_tool(
        name="Copper Sulfate",
        summary="Update Copper Sulfate",
        usage_sheet="Sheet 2",
        tool_context=tool_context,
    )

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Updates for different phytosanitary products should each be stored as independent confirmations",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_phytosanitary_func(captured_update):
    def update_phytosanitary(name: str, phytosanitary_data: dict) -> None:
        captured_update["name"] = name
        captured_update["phytosanitary_data"] = phytosanitary_data

    return update_phytosanitary


@pytest.fixture
def get_phytosanitary_by_name_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return Phytosanitary(name=name, usage_sheet="Sheet", recommended_for="Plagas")

    return get_phytosanitary_by_name


@pytest.fixture
def get_phytosanitary_by_name_not_found():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return None

    return get_phytosanitary_by_name


@pytest.fixture
def update_tool(update_phytosanitary_func, get_phytosanitary_by_name_func, confirmation_store):
    return create_confirm_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def update_tool_not_found(update_phytosanitary_func, get_phytosanitary_by_name_not_found, confirmation_store):
    return create_confirm_update_phytosanitary_tool(
        update_phytosanitary_func=update_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_not_found,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(update_tool, tool_context, confirmation_store):
    update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
        tool_context=tool_context,
    )
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_update(update_tool, tool_context, confirmation_store, captured_update):
    update_tool(
        name="Neem Oil",
        summary="Update Neem Oil",
        usage_sheet="New instructions",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_update


@pytest.fixture
def executed_update_with_target(update_tool, tool_context, confirmation_store, captured_update):
    update_tool(
        name="Neem Oil",
        summary="Update Neem Oil target",
        target="Aphids",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_update
