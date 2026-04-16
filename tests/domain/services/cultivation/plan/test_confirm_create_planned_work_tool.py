import pytest

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.confirm_create_planned_work_tool import (
    create_confirm_create_planned_work_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_name_is_empty(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan fertilization", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_name_required"}, \
        "Empty bonsai name should return a bonsai_name_required error"


@pytest.mark.asyncio
async def should_return_error_when_work_type_is_empty(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="Kaze", work_type="", scheduled_date="2026-03-15", summary="Plan work", tool_context=tool_context)

    assert result == {"status": "error", "message": "work_type_required"}, \
        "Empty work_type should return a work_type_required error"


@pytest.mark.asyncio
async def should_return_error_when_scheduled_date_is_empty(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="", summary="Plan fertilization", tool_context=tool_context)

    assert result == {"status": "error", "message": "scheduled_date_required"}, \
        "Empty scheduled_date should return a scheduled_date_required error"


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="UnknownBonsai", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan fertilization", tool_context=tool_context)

    assert result == {"status": "error", "message": "bonsai_not_found"}, \
        "Unknown bonsai name should return a bonsai_not_found error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_name_missing_for_fertilizer_type(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan fertilization", fertilizer_name="", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_name_required"}, \
        "Missing fertilizer_name for fertilizer_application should return an error"


@pytest.mark.asyncio
async def should_return_error_when_fertilizer_not_found(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan fertilization", fertilizer_name="UnknownFertilizer", tool_context=tool_context)

    assert result == {"status": "error", "message": "fertilizer_not_found"}, \
        "Unknown fertilizer name should return a fertilizer_not_found error"


@pytest.mark.asyncio
async def should_create_planned_work_with_correct_payload_when_user_confirms(create_planned_work_tool, tool_context, captured_planned_works):
    await create_planned_work_tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan BioGrow for Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_planned_works[0].payload == {"fertilizer_id": 1, "fertilizer_name": "BioGrow", "amount": "5 ml"}, \
        "Created planned work should have the correct fertilizer payload"


@pytest.mark.asyncio
async def should_return_success_when_user_confirms(create_planned_work_tool, tool_context):
    result = await create_planned_work_tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan BioGrow for Kaze", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert result["status"] == "success", \
        "Tool should return success status when user confirms"


@pytest.mark.asyncio
async def should_not_create_when_user_cancels(tool_context, captured_planned_works, get_bonsai_by_name_func, get_fertilizer_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func):
    tool = create_confirm_create_planned_work_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, ask_confirmation_cancel)
    await tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan BioGrow", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

    assert captured_planned_works == [], \
        "create_planned_work_func should not be called when user cancels"


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, get_fertilizer_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func):
    tool = create_confirm_create_planned_work_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, ask_confirmation_cancel)
    result = await tool(bonsai_name="Kaze", work_type="fertilizer_application", scheduled_date="2026-03-15", summary="Plan BioGrow", fertilizer_name="BioGrow", amount="5 ml", tool_context=tool_context)

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
def get_phytosanitary_by_name_func():
    def get_phytosanitary_by_name(name: str):
        return None

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
def create_planned_work_tool(get_bonsai_by_name_func, get_fertilizer_by_name_func, get_phytosanitary_by_name_func, create_planned_work_func, ask_confirmation_confirm):
    return create_confirm_create_planned_work_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_fertilizer_by_name_func=get_fertilizer_by_name_func,
        get_phytosanitary_by_name_func=get_phytosanitary_by_name_func,
        create_planned_work_func=create_planned_work_func,
        ask_confirmation=ask_confirmation_confirm,
    )
