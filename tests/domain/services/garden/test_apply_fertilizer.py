import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.garden.apply_fertilizer import (
    create_apply_fertilizer_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(apply_fertilizer_tool, tool_context):
    result = await apply_fertilizer_tool(bonsai_name="", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Empty bonsai name should return bonsai_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_name_is_empty(apply_fertilizer_tool, tool_context):
    result = await apply_fertilizer_tool(bonsai_name="Kaze", fertilizer_name="", amount="5 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Empty fertilizer name should return fertilizer_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_amount_is_empty(apply_fertilizer_tool, tool_context):
    result = await apply_fertilizer_tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="", tool_context=tool_context)

    assert result == {"status": "error", "message": "amount_required"}, \
        "Empty amount should return amount_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(apply_fertilizer_tool, tool_context):
    result = await apply_fertilizer_tool(bonsai_name="Unknown", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_not_found"}, \
        "Unknown bonsai name should return bonsai_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(apply_fertilizer_tool, tool_context):
    result = await apply_fertilizer_tool(bonsai_name="Kaze", fertilizer_name="Unknown", amount="5 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_not_found"}, \
        "Unknown fertilizer name should return fertilizer_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_name, fertilizer_name, amount):
        captured_calls.append((bonsai_name, fertilizer_name, amount))
        return "confirmation text"

    tool = create_apply_fertilizer_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_calls == [("Kaze", "BioGrow", "5 ml")], \
        "build_confirmation_message should be called with bonsai_name, fertilizer_name, and amount"


@pytest.mark.asyncio
async def should_record_fertilizer_event_when_user_confirms(apply_fertilizer_tool, tool_context, captured_events):
    await apply_fertilizer_tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_events[0].event_type == "fertilizer_application", \
        "Should record a fertilizer_application event when user confirms"


@pytest.mark.asyncio
async def should_record_event_with_correct_payload_when_user_confirms(apply_fertilizer_tool, tool_context, captured_events):
    await apply_fertilizer_tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_events[0].payload == {"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"}, \
        "Recorded event should contain fertilizer id, name and amount"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(apply_fertilizer_tool, tool_context):
    result = await apply_fertilizer_tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_record_event_when_user_cancels(tool_context, captured_events, get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, build_confirmation_message):
    tool = create_apply_fertilizer_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_events == [], \
        "record_bonsai_event_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, build_confirmation_message):
    tool = create_apply_fertilizer_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(bonsai_name="Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


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
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def ask_confirmation_confirm():
    async def ask_confirmation(question, tool_context=None):
        return True

    return ask_confirmation


@pytest.fixture
def build_confirmation_message():
    def build(bonsai_name, fertilizer_name, amount):
        return f"Confirm apply '{fertilizer_name}' ({amount}) to '{bonsai_name}'"

    return build


@pytest.fixture
def apply_fertilizer_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, ask_confirmation_confirm, build_confirmation_message):
    return create_apply_fertilizer_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, record_bonsai_event_func, ask_confirmation_confirm, build_confirmation_message)
