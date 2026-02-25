import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.garden.confirm_apply_fertilizer_tool import (
    create_confirm_apply_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(apply_fertilizer_tool):
    result = apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow to Kaze",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_bonsai_name_is_empty(apply_fertilizer_tool, tool_context):
    result = apply_fertilizer_tool(
        bonsai_name="",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai name should return a bonsai_name_required error",
    )


def should_return_error_when_fertilizer_name_is_empty(apply_fertilizer_tool, tool_context):
    result = apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="",
        amount="5 ml",
        summary="Apply fertilizer",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_name_required"}),
        "Empty fertilizer name should return a fertilizer_name_required error",
    )


def should_return_error_when_amount_is_empty(apply_fertilizer_tool, tool_context):
    result = apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="BioGrow",
        amount="",
        summary="Apply BioGrow",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "amount_required"}),
        "Empty amount should return an amount_required error",
    )


def should_return_error_when_bonsai_not_found(apply_fertilizer_tool, tool_context):
    result = apply_fertilizer_tool(
        bonsai_name="UnknownBonsai",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow to UnknownBonsai",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return a bonsai_not_found error",
    )


def should_return_error_when_fertilizer_not_found(apply_fertilizer_tool, tool_context):
    result = apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="UnknownFertilizer",
        amount="5 ml",
        summary="Apply UnknownFertilizer to Kaze",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "fertilizer_not_found"}),
        "Unknown fertilizer name should return a fertilizer_not_found error",
    )


def should_return_confirmation_pending_when_valid(apply_fertilizer_tool, tool_context):
    result = apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow 5 ml to Kaze",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Apply BioGrow 5 ml to Kaze",
        }),
        "Valid input should return a confirmation_pending dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    apply_fertilizer_tool, tool_context, confirmation_store
):
    apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow 5 ml to Kaze",
        tool_context=tool_context,
    )

    assert_that(
        confirmation_store.get_pending("user-123"),
        not_none(),
        "Pending confirmation should be stored in the store",
    )


def should_record_fertilizer_event_on_execution(
    apply_fertilizer_tool, tool_context, confirmation_store, captured_events
):
    apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow 5 ml to Kaze",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    recorded_event = captured_events[0]
    assert_that(
        recorded_event.event_type,
        equal_to("fertilizer_application"),
        "Executed confirmation should record a fertilizer_application event",
    )


def should_record_event_with_correct_payload_on_execution(
    apply_fertilizer_tool, tool_context, confirmation_store, captured_events
):
    apply_fertilizer_tool(
        bonsai_name="Kaze",
        fertilizer_name="BioGrow",
        amount="5 ml",
        summary="Apply BioGrow 5 ml to Kaze",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    recorded_event = captured_events[0]
    assert_that(
        recorded_event.payload,
        equal_to({"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"}),
        "Recorded event payload should contain the fertilizer id, name and amount",
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
def existing_fertilizer():
    return Fertilizer(id=1, name="BioGrow")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    return get_bonsai_by_name


@pytest.fixture
def get_fertilizer_by_name_func(existing_fertilizer):
    def get_fertilizer_by_name(name: str) -> Fertilizer | None:
        return existing_fertilizer if name == existing_fertilizer.name else None

    return get_fertilizer_by_name


@pytest.fixture
def apply_fertilizer_tool(
    get_bonsai_by_name_func,
    get_fertilizer_by_name_func,
    record_bonsai_event_func,
    confirmation_store,
):
    return create_confirm_apply_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")
