import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.storekeeper.fertilizers.confirm_create_fertilizer_tool import (
    create_confirm_create_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(create_tool):
    result = create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(create_tool):
    result = create_tool(
        name="GreenBoom",
        summary="Create GreenBoom",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_name_is_missing(create_tool, tool_context):
    result = create_tool(name="", summary="Create fertilizer", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_name_required"}),
        "Missing name should return a fertilizer_name_required error",
    )


def should_return_error_when_fertilizer_already_exists(create_tool_with_existing, tool_context):
    result = create_tool_with_existing(
        name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_already_exists"}),
        "Existing fertilizer should return a fertilizer_already_exists error",
    )


def should_return_confirmation_summary_when_create_is_valid(create_tool, tool_context):
    result = create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Create GreenBoom",
        }),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(create_tool, tool_context, confirmation_store):
    create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)

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


def should_execute_create_with_usage_sheet_from_searcher(executed_create):
    assert_that(
        executed_create["fertilizer"].usage_sheet,
        equal_to("Apply 5 ml per litre of water."),
        "Executor should pass the usage_sheet returned by the searcher",
    )


def should_deduplicate_second_create_for_same_fertilizer(
    create_tool, tool_context, confirmation_store
):
    create_tool(name="GreenBoom", summary="First create", tool_context=tool_context)
    create_tool(name="GreenBoom", summary="Second create", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(1),
        "Second create for the same fertilizer should be deduplicated, leaving only one confirmation",
    )


def should_store_both_creates_for_different_fertilizers(
    create_tool, tool_context, confirmation_store
):
    create_tool(name="GreenBoom", summary="First create", tool_context=tool_context)
    create_tool(name="BlueForce", summary="Second create", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Creates for different fertilizers should each be stored as independent confirmations",
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
def searcher():
    def search(query: str) -> dict:
        return {"answer": "Apply 5 ml per litre of water.", "results": []}

    return search


@pytest.fixture
def get_fertilizer_by_name_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return None

    return get_fertilizer_by_name


@pytest.fixture
def existing_fertilizer_func():
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return Fertilizer(name=name, usage_sheet="Old sheet", recommended_amount="5 ml/L")

    return get_fertilizer_by_name


@pytest.fixture
def create_tool(create_fertilizer_func, get_fertilizer_by_name_func, searcher, confirmation_store):
    return create_confirm_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        searcher=searcher,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def create_tool_with_existing(create_fertilizer_func, existing_fertilizer_func, searcher, confirmation_store):
    return create_confirm_create_fertilizer_tool(
        create_fertilizer_func=create_fertilizer_func,
        get_fertilizer_by_name_func=existing_fertilizer_func,
        searcher=searcher,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(create_tool, tool_context, confirmation_store):
    create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_create(create_tool, tool_context, confirmation_store, captured_create):
    create_tool(name="GreenBoom", summary="Create GreenBoom", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_create
