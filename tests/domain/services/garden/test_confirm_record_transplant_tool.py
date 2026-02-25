import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.garden.confirm_record_transplant_tool import (
    create_confirm_record_transplant_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(record_transplant_tool):
    result = record_transplant_tool(
        bonsai_name="Kaze",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant Kaze to 20 cm pot",
        tool_context=None,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_bonsai_name_is_empty(record_transplant_tool, tool_context):
    result = record_transplant_tool(
        bonsai_name="",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai name should return a bonsai_name_required error",
    )


def should_return_error_when_bonsai_not_found(record_transplant_tool, tool_context):
    result = record_transplant_tool(
        bonsai_name="UnknownBonsai",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant UnknownBonsai",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return a bonsai_not_found error",
    )


def should_return_confirmation_pending_when_valid(record_transplant_tool, tool_context):
    result = record_transplant_tool(
        bonsai_name="Kaze",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant Kaze to 20 cm pot with akadama y pomice",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": "Transplant Kaze to 20 cm pot with akadama y pomice",
        }),
        "Valid input should return a confirmation_pending dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    record_transplant_tool, tool_context, confirmation_store
):
    record_transplant_tool(
        bonsai_name="Kaze",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant Kaze to 20 cm pot",
        tool_context=tool_context,
    )

    assert_that(
        confirmation_store.get_pending("user-123"),
        not_none(),
        "Pending confirmation should be stored in the store",
    )


def should_record_transplant_event_on_execution(
    record_transplant_tool, tool_context, confirmation_store, captured_events
):
    record_transplant_tool(
        bonsai_name="Kaze",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant Kaze to 20 cm pot",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    recorded_event = captured_events[0]
    assert_that(
        recorded_event.event_type,
        equal_to("transplant"),
        "Executed confirmation should record a transplant event",
    )


def should_record_event_with_correct_payload_on_execution(
    record_transplant_tool, tool_context, confirmation_store, captured_events
):
    record_transplant_tool(
        bonsai_name="Kaze",
        pot_size="20 cm",
        pot_type="cerámica",
        substrate="akadama y pomice",
        summary="Transplant Kaze to 20 cm pot",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    recorded_event = captured_events[0]
    assert_that(
        recorded_event.payload,
        equal_to({"pot_size": "20 cm", "pot_type": "cerámica", "substrate": "akadama y pomice"}),
        "Recorded event payload should contain pot size, pot type and substrate",
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
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    return get_bonsai_by_name


@pytest.fixture
def record_transplant_tool(
    get_bonsai_by_name_func,
    record_bonsai_event_func,
    confirmation_store,
):
    return create_confirm_record_transplant_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        record_bonsai_event_func=record_bonsai_event_func,
        confirmation_store=confirmation_store,
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")
