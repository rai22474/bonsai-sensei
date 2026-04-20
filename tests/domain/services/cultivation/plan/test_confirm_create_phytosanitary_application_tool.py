import pytest

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.confirm_create_phytosanitary_application_tool import (
    create_confirm_create_phytosanitary_application_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


class MockPhytosanitary:
    def __init__(self, phytosanitary_id: int, name: str):
        self.id = phytosanitary_id
        self.name = name


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(phytosanitary_tool, tool_context):
    result = await phytosanitary_tool(bonsai_name="", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Empty bonsai name should return a bonsai_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_scheduled_date_is_empty(phytosanitary_tool, tool_context):
    result = await phytosanitary_tool(bonsai_name="Kaze", scheduled_date="", phytosanitary_name="Neem Oil", tool_context=tool_context)

    assert result == {"status": "error", "message": "scheduled_date_required"}, \
        "Empty scheduled_date should return a scheduled_date_required error"


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_name_is_empty(phytosanitary_tool, tool_context):
    result = await phytosanitary_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_name_required"}, \
        "Empty phytosanitary_name should return a phytosanitary_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(phytosanitary_tool, tool_context):
    result = await phytosanitary_tool(bonsai_name="UnknownBonsai", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_not_found"}, \
        "Unknown bonsai name should return a bonsai_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_phytosanitary_not_found(phytosanitary_tool, tool_context):
    result = await phytosanitary_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="UnknownProduct", tool_context=tool_context)

    assert result == {"status": "error", "message": "phytosanitary_not_found"}, \
        "Unknown phytosanitary name should return a phytosanitary_not_found error"


@pytest.mark.asyncio
async def should_build_confirmation_message_with_correct_args(tool_context, get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, ask_confirmation_confirm):
    captured_calls = []

    def build_confirmation_message(bonsai_name, phytosanitary_name, amount, scheduled_date):
        captured_calls.append((bonsai_name, phytosanitary_name, amount, scheduled_date))
        return "confirmation text"

    tool = create_confirm_create_phytosanitary_application_tool(
        get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func,
        ask_confirmation_confirm, build_confirmation_message,
    )
    await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", amount="2 ml", tool_context=tool_context)

    assert captured_calls == [("Kaze", "Neem Oil", "2 ml", "2026-03-15")], \
        "build_confirmation_message should be called with bonsai_name, phytosanitary_name, amount, scheduled_date"


@pytest.mark.asyncio
async def should_create_with_correct_payload_when_user_confirms(phytosanitary_tool, tool_context, captured_planned_works):
    await phytosanitary_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", amount="2 ml", tool_context=tool_context)

    assert captured_planned_works[0].payload == {"phytosanitary_id": 1, "phytosanitary_name": "Neem Oil", "amount": "2 ml"}, \
        "Created planned work should have the correct phytosanitary payload"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(phytosanitary_tool, tool_context):
    result = await phytosanitary_tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", amount="2 ml", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_planned_works, get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, build_confirmation_message):
    tool = create_confirm_create_phytosanitary_application_tool(
        get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func,
        ask_confirmation_cancel, build_confirmation_message,
    )
    await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", amount="2 ml", tool_context=tool_context)

    assert captured_planned_works == [], \
        "create_planned_work_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, build_confirmation_message):
    tool = create_confirm_create_phytosanitary_application_tool(
        get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func,
        ask_confirmation_cancel, build_confirmation_message,
    )
    result = await tool(bonsai_name="Kaze", scheduled_date="2026-03-15", phytosanitary_name="Neem Oil", amount="2 ml", tool_context=tool_context)

    assert result["status"] == "cancelled", \
        "Tool should return cancelled status when user declines"


async def ask_confirmation_cancel(question, tool_context=None):
    return False


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
def existing_phytosanitary():
    return MockPhytosanitary(phytosanitary_id=1, name="Neem Oil")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    return get_bonsai_by_name


@pytest.fixture
def get_phytosanitary_by_name_func(existing_phytosanitary):
    def get_phytosanitary_by_name(name: str):
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
    def build(bonsai_name, phytosanitary_name, amount, scheduled_date):
        return f"Confirm {phytosanitary_name} for {bonsai_name}"

    return build


@pytest.fixture
def phytosanitary_tool(get_bonsai_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, ask_confirmation_confirm, build_confirmation_message):
    return create_confirm_create_phytosanitary_application_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        create_planned_work_func=create_planned_work_func,
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_confirmation_message,
    )
