import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.garden.confirm_apply_phytosanitary_tool import (
    create_confirm_apply_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(apply_phytosanitary_tool):
    result = apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio to Kaze",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_bonsai_name_is_empty(apply_phytosanitary_tool, tool_context):
    result = apply_phytosanitary_tool(
        bonsai_name="",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai name should return a bonsai_name_required error",
    )


def should_return_error_when_phytosanitary_name_is_empty(apply_phytosanitary_tool, tool_context):
    result = apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="",
        amount="3 ml",
        summary="Apply treatment",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_name_required"}),
        "Empty phytosanitary name should return a phytosanitary_name_required error",
    )


def should_return_error_when_amount_is_empty(apply_phytosanitary_tool, tool_context):
    result = apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="NimBio",
        amount="",
        summary="Apply NimBio",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "amount_required"}),
        "Empty amount should return an amount_required error",
    )


def should_return_error_when_bonsai_not_found(apply_phytosanitary_tool, tool_context):
    result = apply_phytosanitary_tool(
        bonsai_name="UnknownBonsai",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio to UnknownBonsai",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return a bonsai_not_found error",
    )


def should_return_error_when_phytosanitary_not_found(apply_phytosanitary_tool, tool_context):
    result = apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="UnknownProduct",
        amount="3 ml",
        summary="Apply UnknownProduct to Kaze",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "phytosanitary_not_found"}),
        "Unknown phytosanitary name should return a phytosanitary_not_found error",
    )


def should_return_confirmation_pending_when_valid(apply_phytosanitary_tool, tool_context):
    result = apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio 3 ml to Kaze",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Apply NimBio 3 ml to Kaze",
        }),
        "Valid input should return a confirmation_pending dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    apply_phytosanitary_tool, tool_context, confirmation_store
):
    apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio 3 ml to Kaze",
        tool_context=tool_context,
    )

    assert_that(
        confirmation_store.get_pending("user-123"),
        not_none(),
        "Pending confirmation should be stored in the store",
    )


def should_record_phytosanitary_event_on_execution(
    apply_phytosanitary_tool, tool_context, confirmation_store, captured_events
):
    apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio 3 ml to Kaze",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    recorded_event = captured_events[0]
    assert_that(
        recorded_event.event_type,
        equal_to("phytosanitary_application"),
        "Executed confirmation should record a phytosanitary_application event",
    )


def should_record_event_with_correct_payload_on_execution(
    apply_phytosanitary_tool, tool_context, confirmation_store, captured_events
):
    apply_phytosanitary_tool(
        bonsai_name="Kaze",
        phytosanitary_name="NimBio",
        amount="3 ml",
        summary="Apply NimBio 3 ml to Kaze",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    recorded_event = captured_events[0]
    assert_that(
        recorded_event.payload,
        equal_to({"phytosanitary_name": "NimBio", "amount": "3 ml"}),
        "Recorded event payload should contain the phytosanitary name and amount",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


@pytest.fixture
def captured_events():
    return []


@pytest.fixture
def record_bonsai_event_func(captured_events):
    def record_bonsai_event(bonsai_event: BonsaiEvent) -> BonsaiEvent:
        captured_events.append(bonsai_event)
        return bonsai_event

    return record_bonsai_event


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Kaze", species_id=1)


@pytest.fixture
def existing_phytosanitary():
    return Phytosanitary(id=1, name="NimBio")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    return get_bonsai_by_name


@pytest.fixture
def get_phytosanitary_by_name_func(existing_phytosanitary):
    def get_phytosanitary_by_name(name: str) -> Phytosanitary | None:
        return existing_phytosanitary if name == existing_phytosanitary.name else None

    return get_phytosanitary_by_name


@pytest.fixture
def apply_phytosanitary_tool(
    get_bonsai_by_name_func,
    get_phytosanitary_by_name_func,
    record_bonsai_event_func,
    confirmation_store,
):
    return create_confirm_apply_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")
