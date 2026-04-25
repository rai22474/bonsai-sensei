import pytest

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.create_fertilizer_application import (
    create_create_fertilizer_application_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(fertilizer_tool, tool_context):
    result = await fertilizer_tool(bonsai_name="", scheduled_date="2026-03-15", fertilizer_name="BioGrow", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Empty bonsai name should return a bonsai_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_scheduled_date_is_empty(fertilizer_tool, tool_context):
    result = await fertilizer_tool(bonsai_name="Kaze", scheduled_date="", fertilizer_name="BioGrow", tool_context=tool_context)

    assert result == {"status": "error", "message": "scheduled_date_required"}, \
        "Empty scheduled_date should return a scheduled_date_required error"


@pytest.mark.asyncio
async def should_use_next_saturday_when_scheduled_date_is_empty(fertilizer_tool, tool_context, captured_planned_works):
    tool_context.state["next_saturday"] = "2026-05-03"

    await fertilizer_tool(bonsai_name="Kaze", scheduled_date="", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    from datetime import date
    assert captured_planned_works[0].scheduled_date == date(2026, 5, 3), \
        "When scheduled_date is empty, the tool should fall back to next_saturday from session state"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_name_is_empty(fertilizer_tool, tool_context):
    result = await fertilizer_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Empty fertilizer_name should return a fertilizer_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(fertilizer_tool, tool_context):
    result = await fertilizer_tool(bonsai_name="UnknownBonsai", scheduled_date="2026-03-15", fertilizer_name="BioGrow", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_not_found"}, \
        "Unknown bonsai name should return a bonsai_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(fertilizer_tool, tool_context):
    result = await fertilizer_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="UnknownFertilizer", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_not_found"}, \
        "Unknown fertilizer name should return a fertilizer_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_name, fertilizer_name, amount, scheduled_date):
        captured_calls.append((bonsai_name, fertilizer_name, amount, scheduled_date))
        return "confirmation text"

    tool = create_create_fertilizer_application_tool(
        get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func,
        ask_confirmation_confirm, build_confirmation_message,
    )
    await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_calls == [("Kaze", "BioGrow", "5 ml", "2026-03-15")], \
        "build_confirmation_message should be called with bonsai_name, fertilizer_name, amount, scheduled_date"


@pytest.mark.asyncio
async def should_create_with_correct_payload_when_user_confirms(fertilizer_tool, tool_context, captured_planned_works):
    await fertilizer_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_planned_works[0].payload == {"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"}, \
        "Created planned work should have the correct fertilizer payload"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(fertilizer_tool, tool_context):
    result = await fertilizer_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_planned_works, get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func, build_confirmation_message):
    tool = create_create_fertilizer_application_tool(
        get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func,
        ask_confirmation_cancel, build_confirmation_message,
    )
    await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_planned_works == [], \
        "create_planned_work_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func, build_confirmation_message):
    tool = create_create_fertilizer_application_tool(
        get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func,
        ask_confirmation_cancel, build_confirmation_message,
    )
    result = await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def captured_planned_works():
    return []


@pytest.fixture
def create_planned_work_func(captured_planned_works):
    def create_planned_work(planned_work: PlannedWork) -> PlannedWork:
        captured_planned_works.append(planned_work)
        return planned_work

    return create_planned_work


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
    def build(bonsai_name, fertilizer_name, amount, scheduled_date):
        return f"Confirm fertilizer {fertilizer_name} for {bonsai_name}"

    return build


@pytest.fixture
def fertilizer_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, create_planned_work_func, ask_confirmation_confirm, build_confirmation_message):
    return create_create_fertilizer_application_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        create_planned_work_func=create_planned_work_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
