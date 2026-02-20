import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_create_phytosanitary_tool import (
    create_confirm_create_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(create_tool):
    result = create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(create_tool):
    result = create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
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
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create product",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Missing name should return a phytosanitary_name_required error",
    )


def should_return_error_when_usage_sheet_is_missing(create_tool, tool_context):
    result = create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="",
        summary="Create Neem Oil",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "usage_sheet_required"}),
        "Missing usage_sheet should return a usage_sheet_required error",
    )


def should_return_error_when_target_is_missing(create_tool, tool_context):
    result = create_tool(
        name="Neem Oil",
        target="",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "recommended_for_required"}),
        "Missing target should return a recommended_for_required error",
    )


def should_return_confirmation_summary_when_create_is_valid(create_tool, tool_context):
    result = create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"confirmation": "Create Neem Oil"}),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(create_tool, tool_context, confirmation_store):
    create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
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
        equal_to("Create Neem Oil"),
        "Stored confirmation summary should match the argument",
    )


def should_execute_create_with_correct_name(executed_create):
    assert_that(
        executed_create["phytosanitary"].name,
        equal_to("Neem Oil"),
        "Executor should pass the correct name to create_phytosanitary_func",
    )


def should_execute_create_with_correct_target(executed_create):
    assert_that(
        executed_create["phytosanitary"].recommended_for,
        equal_to("Spider mites"),
        "Executor should pass the correct target as recommended_for to create_phytosanitary_func",
    )


def should_store_both_confirmations_when_created_twice(
    create_tool, tool_context, confirmation_store
):
    create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="First create",
        tool_context=tool_context,
    )
    create_tool(
        name="Copper Sulfate",
        target="Fungal disease",
        usage_sheet="Apply weekly",
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
def create_phytosanitary_func(captured_create):
    def create_phytosanitary(phytosanitary) -> None:
        captured_create["phytosanitary"] = phytosanitary

    return create_phytosanitary


@pytest.fixture
def create_tool(create_phytosanitary_func, confirmation_store):
    return create_confirm_create_phytosanitary_tool(create_phytosanitary_func, confirmation_store)


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(create_tool, tool_context, confirmation_store):
    create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
        tool_context=tool_context,
    )
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_create(create_tool, tool_context, confirmation_store, captured_create):
    create_tool(
        name="Neem Oil",
        target="Spider mites",
        usage_sheet="Dilute 5ml per liter",
        summary="Create Neem Oil",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_create
