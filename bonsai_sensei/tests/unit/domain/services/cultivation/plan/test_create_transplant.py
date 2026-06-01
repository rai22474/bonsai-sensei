import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.create_transplant import (
    create_create_transplant_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(transplant_tool, tool_context):
    result = await transplant_tool(bonsai_name="", scheduled_date="2026-03-15", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai name should return a bonsai_name_required error")


@pytest.mark.asyncio
async def should_return_error_when_scheduled_date_is_empty(transplant_tool, tool_context):
    result = await transplant_tool(bonsai_name="Kaze", scheduled_date="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "scheduled_date_required"}),
        "Empty scheduled_date should return a scheduled_date_required error")


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(transplant_tool, tool_context):
    result = await transplant_tool(bonsai_name="UnknownBonsai", scheduled_date="2026-03-15", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return a bonsai_not_found error")


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, get_bonsai_by_name_func, create_planned_work_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_name, scheduled_date, pot_size, pot_type, substrate):
        captured_calls.append((bonsai_name, scheduled_date, pot_size, pot_type, substrate))
        return "confirmation text"

    tool = create_create_transplant_tool(
        get_bonsai_by_name_func, create_planned_work_func,
        ask_confirmation_confirm, build_confirmation_message,
    )
    await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", pot_size="20 cm", pot_type="ceramic", substrate="akadama", tool_context=tool_context)

    assert_that(captured_calls, equal_to([("Kaze", "2026-03-15", "20 cm", "ceramic", "akadama")]),
        "build_confirmation_message should be called with bonsai_name, scheduled_date, pot_size, pot_type, substrate")


@pytest.mark.asyncio
async def should_create_with_correct_payload_when_user_confirms(transplant_tool, tool_context, captured_planned_works):
    await transplant_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", pot_size="20 cm", pot_type="ceramic", substrate="akadama", tool_context=tool_context)

    assert_that(captured_planned_works[0].payload, equal_to({"pot_size": "20 cm", "pot_type": "ceramic", "substrate": "akadama"}),
        "Created planned work should have the correct transplant payload")


@pytest.mark.asyncio
async def should_create_with_partial_payload_when_optional_fields_missing(transplant_tool, tool_context, captured_planned_works):
    await transplant_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", pot_size="20 cm", tool_context=tool_context)

    assert_that(captured_planned_works[0].payload, equal_to({"pot_size": "20 cm"}),
        "Created planned work payload should only include provided optional fields")


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(transplant_tool, tool_context):
    result = await transplant_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_planned_works, get_bonsai_by_name_func, create_planned_work_func, build_confirmation_message):
    tool = create_create_transplant_tool(
        get_bonsai_by_name_func, create_planned_work_func,
        ask_confirmation_cancel, build_confirmation_message,
    )
    await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", tool_context=tool_context)

    assert_that(captured_planned_works, equal_to([]),
        "create_planned_work_func should not be called when user cancels")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, create_planned_work_func, build_confirmation_message):
    tool = create_create_transplant_tool(
        get_bonsai_by_name_func, create_planned_work_func,
        ask_confirmation_cancel, build_confirmation_message,
    )
    result = await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled status when user declines")


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
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    return get_bonsai_by_name


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
    def build(bonsai_name, scheduled_date, pot_size, pot_type, substrate):
        return f"Confirm transplant for {bonsai_name}"

    return build


@pytest.fixture
def transplant_tool(get_bonsai_by_name_func, create_planned_work_func, ask_confirmation_confirm, build_confirmation_message):
    return create_create_transplant_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        create_planned_work_func=create_planned_work_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
