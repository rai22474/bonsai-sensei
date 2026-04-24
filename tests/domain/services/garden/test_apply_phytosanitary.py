import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.garden.confirm_apply_phytosanitary_tool import (
    create_confirm_apply_phytosanitary_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(apply_phytosanitary_tool, tool_context):
    result = await apply_phytosanitary_tool(bonsai_name="", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Empty bonsai name should return bonsai_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_name_is_empty(apply_phytosanitary_tool, tool_context):
    result = await apply_phytosanitary_tool(bonsai_name="Kaze", phytosanitary_name="", amount="3 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_name_required"}, \
        "Empty phytosanitary name should return phytosanitary_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_amount_is_empty(apply_phytosanitary_tool, tool_context):
    result = await apply_phytosanitary_tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="", tool_context=tool_context)

    assert result == {"status": "error", "message": "amount_required"}, \
        "Empty amount should return amount_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(apply_phytosanitary_tool, tool_context):
    result = await apply_phytosanitary_tool(bonsai_name="Unknown", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_not_found"}, \
        "Unknown bonsai name should return bonsai_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_not_found(apply_phytosanitary_tool, tool_context):
    result = await apply_phytosanitary_tool(bonsai_name="Kaze", phytosanitary_name="Unknown", amount="3 ml", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_not_found"}, \
        "Unknown phytosanitary name should return phytosanitary_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_name, phytosanitary_name, amount):
        captured_calls.append((bonsai_name, phytosanitary_name, amount))
        return "confirmation text"

    tool = create_confirm_apply_phytosanitary_tool(get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, ask_confirmation_confirm, build_confirmation_message)
    await tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert captured_calls == [("Kaze", "NimBio", "3 ml")], \
        "build_confirmation_message should be called with bonsai_name, phytosanitary_name, and amount"


@pytest.mark.asyncio
async def should_record_phytosanitary_event_when_user_confirms(apply_phytosanitary_tool, tool_context, captured_events):
    await apply_phytosanitary_tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert captured_events[0].event_type == "phytosanitary_application", \
        "Should record a phytosanitary_application event when user confirms"


@pytest.mark.asyncio
async def should_record_event_with_correct_payload_when_user_confirms(apply_phytosanitary_tool, tool_context, captured_events):
    await apply_phytosanitary_tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert captured_events[0].payload == {"phytosanitary_id": 1, "phytosanitary_name": "NimBio", "amount": "3 ml"}, \
        "Recorded event should contain phytosanitary id, name and amount"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(apply_phytosanitary_tool, tool_context):
    result = await apply_phytosanitary_tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_record_event_when_user_cancels(tool_context, captured_events, get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, build_confirmation_message):
    tool = create_confirm_apply_phytosanitary_tool(get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, ask_confirmation_cancel, build_confirmation_message)
    await tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

    assert captured_events == [], \
        "record_bonsai_event_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, build_confirmation_message):
    tool = create_confirm_apply_phytosanitary_tool(get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, ask_confirmation_cancel, build_confirmation_message)
    result = await tool(bonsai_name="Kaze", phytosanitary_name="NimBio", amount="3 ml", tool_context=tool_context)

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
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def ask_confirmation_confirm():
    async def ask_confirmation(question, tool_context=None):
        return True

    return ask_confirmation


@pytest.fixture
def build_confirmation_message():
    def build(bonsai_name, phytosanitary_name, amount):
        return f"Confirm apply '{phytosanitary_name}' ({amount}) to '{bonsai_name}'"

    return build


@pytest.fixture
def apply_phytosanitary_tool(get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_apply_phytosanitary_tool(get_bonsai_by_name_func, get_phytosanitary_by_name_func, record_bonsai_event_func, ask_confirmation_confirm, build_confirmation_message)
