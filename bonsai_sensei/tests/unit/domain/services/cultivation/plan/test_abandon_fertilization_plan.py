from datetime import date, datetime, timezone
import pytest
from hamcrest import assert_that, equal_to, contains_string

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilization_plan import FertilizationPlan
from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.domain.services.cultivation.plan.fertilization.abandon_plan import (
    create_abandon_fertilization_plan_tool,
)


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


class MockToolContext:
    def __init__(self, user_id="user-123"):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(tool, tool_context):
    result = await tool(bonsai_name="Unknown", reason="No longer needed", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_no_active_plan(tool_context, get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    result = await tool(bonsai_name="Shikamaru", reason="Not needed", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "no_active_plan"}),
        "Should return no_active_plan when the bonsai has no active plan")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(tool_context, get_bonsai_by_name_func, build_abandon_confirmation_message, read_wiki_page_func):
    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_confirmation=ask_confirmation_cancel,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    result = await tool(bonsai_name="Shikamaru", reason="Change of plans", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"), "Should return cancelled when user declines")


@pytest.mark.asyncio
async def should_mark_plan_as_abandoned_on_confirm(tool_context, get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    updated_plans = []

    def update_plan(plan: FertilizationPlan) -> FertilizationPlan:
        updated_plans.append(plan)
        return plan

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=update_plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name="Shikamaru", reason="Changed strategy", tool_context=tool_context)

    assert_that(len(updated_plans), equal_to(1), "Plan should be updated once")
    assert_that(updated_plans[0].status, equal_to("abandoned"), "Plan status should be 'abandoned'")
    assert_that(updated_plans[0].abandonment_reason, equal_to("Changed strategy"), "Abandonment reason should be recorded")


@pytest.mark.asyncio
async def should_delete_future_works_on_confirm(tool_context, get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    deleted_calls = []

    def delete_future_works(plan_id, cutoff_date):
        deleted_calls.append((plan_id, cutoff_date))
        return 2

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=delete_future_works,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name="Shikamaru", reason="Changed strategy", tool_context=tool_context)

    assert_that(len(deleted_calls), equal_to(1), "delete_future_works should be called once")
    assert_that(deleted_calls[0][0], equal_to(7), "Should delete works for the correct plan id")


@pytest.mark.asyncio
async def should_update_wiki_page_with_abandonment_section_on_confirm(tool_context, get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    written_pages = {}

    tool = create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: written_pages.update({path: content}) or {"status": "success"},
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )

    await tool(bonsai_name="Shikamaru", reason="Changed strategy", tool_context=tool_context)

    wiki_path = "bonsai/shikamaru/plans/2026-03_to_2026-07.md"
    assert_that(wiki_path in written_pages, equal_to(True), "Wiki page for the plan should be updated")
    assert_that(written_pages[wiki_path], contains_string("Changed strategy"), "Wiki should include abandonment reason")


@pytest.mark.asyncio
async def should_return_success_on_confirm(tool, tool_context):
    result = await tool(bonsai_name="Shikamaru", reason="Changed strategy", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"), "Tool should return success after abandonment")


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False)


@pytest.fixture
def tool_context():
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


@pytest.fixture
def tool(get_bonsai_by_name_func, ask_confirmation_confirm, build_abandon_confirmation_message, read_wiki_page_func):
    return create_abandon_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        get_active_fertilization_plan_func=lambda bonsai_id: _active_plan(),
        update_fertilization_plan_func=lambda plan: plan,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_confirmation=ask_confirmation_confirm,
        build_confirmation_message=build_abandon_confirmation_message,
    )
