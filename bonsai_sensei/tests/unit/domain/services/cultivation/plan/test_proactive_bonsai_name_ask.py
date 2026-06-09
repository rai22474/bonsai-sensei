from datetime import date, datetime, timezone
import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilization_plan import FertilizationPlan
from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.cultivation.plan.fertilization.abandon_plan import (
    create_abandon_fertilization_plan_tool,
)


@pytest.mark.asyncio
async def should_ask_for_bonsai_name_when_not_provided(tool_context, get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    asked_questions = []

    async def ask_human_capture(question, tool_context=None):
        asked_questions.append(question)
        return "Shikamaru"

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_capture,
        build_bonsai_name_question=lambda: "¿Para qué bonsái?",
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name=None, reason="Changed strategy", tool_context=tool_context)

    assert_that(asked_questions, equal_to(["¿Para qué bonsái?"]),
        "ask_human should be called with the bonsai name question when bonsai_name is None")


@pytest.mark.asyncio
async def should_not_ask_for_bonsai_name_when_already_provided(tool_context, get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    asked_questions = []

    async def ask_human_capture(question, tool_context=None):
        asked_questions.append(question)
        return "SomeOtherBonsai"

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_capture,
        build_bonsai_name_question=lambda: "¿Para qué bonsái?",
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name="Shikamaru", reason="Changed strategy", tool_context=tool_context)

    assert_that(asked_questions, equal_to([]),
        "ask_human should not be called when bonsai_name is already provided")


@pytest.mark.asyncio
async def should_use_asked_bonsai_name_to_look_up_bonsai(tool_context, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    resolved_names = []

    def capturing_get_bonsai_by_name(name: str) -> Bonsai | None:
        resolved_names.append(name)
        return Bonsai(id=1, name=name, species_id=1) if name == "Shikamaru" else None

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=capturing_get_bonsai_by_name,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=lambda question, tool_context=None: _async_return("Shikamaru"),
        build_bonsai_name_question=lambda: "¿Para qué bonsái?",
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name=None, reason="Changed strategy", tool_context=tool_context)

    assert_that(resolved_names, equal_to(["Shikamaru"]),
        "get_bonsai_by_name should be called with the name returned by ask_human")


@pytest.mark.asyncio
async def should_not_ask_when_bonsai_name_in_session_state(ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    asked_questions = []

    async def ask_human_capture(question, tool_context=None):
        asked_questions.append(question)
        return "ShouldNotBeUsed"

    class MockToolContextWithState:
        user_id = "user-123"
        state = {"active_bonsai_name": "Shikamaru"}

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=lambda name: Bonsai(id=1, name=name, species_id=1) if name == "Shikamaru" else None,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_capture,
        build_bonsai_name_question=lambda: "¿Para qué bonsái?",
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name=None, reason="Changed strategy", tool_context=MockToolContextWithState())

    assert_that(asked_questions, equal_to([]),
        "ask_human should not be called when active_bonsai_name is already in session state")


@pytest.mark.asyncio
async def should_store_resolved_name_in_session_state(ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    class MockToolContextEmpty:
        user_id = "user-123"
        state = {}

    ctx = MockToolContextEmpty()

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=lambda name: Bonsai(id=1, name=name, species_id=1) if name == "Shikamaru" else None,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=lambda question, tool_context=None: _async_return("Shikamaru"),
        build_bonsai_name_question=lambda: "¿Para qué bonsái?",
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name=None, reason="Changed strategy", tool_context=ctx)

    assert_that(ctx.state.get("active_bonsai_name"), equal_to("Shikamaru"),
        "resolved bonsai name should be stored in session state for reuse by subsequent tools")


async def _async_return(value):
    return value


@pytest.fixture
def tool_context():
    class MockToolContext:
        user_id = "user-123"
        state = {}
    return MockToolContext()


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Shikamaru", species_id=1)


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None
    return get_bonsai_by_name


@pytest.fixture
def ask_confirmation_confirm():
    async def ask_confirmation(question, tool_context=None):
        return ConfirmationResult(accepted=True)
    return ask_confirmation


@pytest.fixture
def build_abandon_confirmation_message():
    return lambda bonsai_name, period_start, period_end, reason: f"Abandon plan for {bonsai_name}?"


@pytest.fixture
def read_wiki_page_func():
    return lambda path: {"status": "error", "message": "page_not_found"}


def _active_plan(bonsai_id=1):
    return FertilizationPlan(
        id=7,
        bonsai_id=bonsai_id,
        period_start=date(2026, 3, 1),
        period_end=date(2026, 7, 31),
        status="active",
        wiki_path="bonsai/shikamaru/plans/2026-03_to_2026-07.md",
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
