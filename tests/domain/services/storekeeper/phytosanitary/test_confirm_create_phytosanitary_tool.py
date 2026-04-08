import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.storekeeper.phytosanitary.confirm_create_phytosanitary_tool import (
    create_confirm_create_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(create_tool):
    result = create_tool(name="Neem Oil", summary="Create Neem Oil", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(create_tool):
    result = create_tool(
        name="Neem Oil",
        summary="Create Neem Oil",
        tool_context=MockToolContext(user_id=None),
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_name_is_missing(create_tool, tool_context):
    result = create_tool(name="", summary="Create product", tool_context=tool_context)

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Missing name should return a phytosanitary_name_required error",
    )


def should_return_error_when_phytosanitary_already_exists(create_tool_with_existing, tool_context):
    result = create_tool_with_existing(
        name="Neem Oil", summary="Create Neem Oil", tool_context=tool_context
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_already_exists"}),
        "Existing product should return a phytosanitary_already_exists error",
    )


def should_return_confirmation_summary_when_create_is_valid(create_tool, tool_context):
    result = create_tool(name="Neem Oil", summary="Create Neem Oil", tool_context=tool_context)

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Create Neem Oil",
        }),
        "Valid input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(create_tool, tool_context, confirmation_store):
    create_tool(name="Neem Oil", summary="Create Neem Oil", tool_context=tool_context)

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


def should_execute_create_with_usage_sheet_from_searcher(executed_create):
    assert_that(
        executed_create["phytosanitary"].usage_sheet,
        equal_to("Dilute 5 ml per litre of water."),
        "Executor should pass the usage_sheet returned by the searcher",
    )


def should_deduplicate_second_create_for_same_phytosanitary(
    create_tool, tool_context, confirmation_store
):
    create_tool(name="Neem Oil", summary="First create", tool_context=tool_context)
    create_tool(name="Neem Oil", summary="Second create", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(1),
        "Second create for the same product should be deduplicated, leaving only one confirmation",
    )


def should_store_both_creates_for_different_phytosanitary_products(
    create_tool, tool_context, confirmation_store
):
    create_tool(name="Neem Oil", summary="First create", tool_context=tool_context)
    create_tool(name="Copper Sulfate", summary="Second create", tool_context=tool_context)

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Creates for different products should each be stored as independent confirmations",
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
def searcher():
    def search(query: str) -> dict:
        return {"answer": "Dilute 5 ml per litre of water.", "results": []}

    return search


@pytest.fixture
def get_phytosanitary_by_name_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return None

    return get_phytosanitary_by_name


@pytest.fixture
def existing_phytosanitary_func():
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return Phytosanitary(name=name, usage_sheet="Old sheet", recommended_for="Plagas")

    return get_phytosanitary_by_name


@pytest.fixture
def create_tool(create_phytosanitary_func, get_phytosanitary_by_name_func, searcher, confirmation_store):
    return create_confirm_create_phytosanitary_tool(
        create_phytosanitary_func=create_phytosanitary_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        searcher=searcher,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def create_tool_with_existing(create_phytosanitary_func, existing_phytosanitary_func, searcher, confirmation_store):
    return create_confirm_create_phytosanitary_tool(
        create_phytosanitary_func=create_phytosanitary_func,
        get_phytosanitary_by_name_func=existing_phytosanitary_func,
        searcher=searcher,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def pending_confirmation(create_tool, tool_context, confirmation_store):
    create_tool(name="Neem Oil", summary="Create Neem Oil", tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_create(create_tool, tool_context, confirmation_store, captured_create):
    create_tool(name="Neem Oil", summary="Create Neem Oil", tool_context=tool_context)
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_create
