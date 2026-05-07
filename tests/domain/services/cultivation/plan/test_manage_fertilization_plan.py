import pytest
from hamcrest import assert_that, equal_to, not_none, contains_string

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilization_plan import FertilizationPlan
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.fertilization.manage import (
    create_manage_fertilization_plan_tool,
)

from datetime import date


class MockToolContext:
    def __init__(self, user_id="user-123"):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(tool):
    result = await tool(bonsai_name="Unknown", start_date="2026-03-01", end_date="2026-07-31")

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_no_fertilizers_available(get_bonsai_by_name_func, tool_context):
    tool = create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=lambda: [],
        get_fertilizer_by_name_func=lambda name: None,
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        create_fertilization_plan_func=lambda plan: plan,
        update_fertilization_plan_func=lambda plan: plan,
        create_planned_work_func=lambda work: work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=stub_run_clarification_loop,
        run_plan_proposal=stub_run_plan_proposal,
    )

    result = await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "no_fertilizers_available"}),
        "Empty fertilizer catalog should return no_fertilizers_available error")


@pytest.mark.asyncio
async def should_return_error_when_start_date_invalid(tool, tool_context):
    result = await tool(bonsai_name="Shikamaru", start_date="not-a-date", end_date="2026-07-31", tool_context=tool_context)

    assert_that(result["status"], equal_to("error"), "Invalid start_date should return error")
    assert_that(result["message"], equal_to("invalid_date_format"), "Should report invalid_date_format")


@pytest.mark.asyncio
async def should_return_error_when_end_date_invalid(tool, tool_context):
    result = await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="not-a-date", tool_context=tool_context)

    assert_that(result["status"], equal_to("error"), "Invalid end_date should return error")
    assert_that(result["message"], equal_to("invalid_date_format"), "Should report invalid_date_format")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines(get_bonsai_by_name_func, list_fertilizers_func, tool_context):
    tool = create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=lambda name: Fertilizer(id=1, name=name),
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        create_fertilization_plan_func=lambda plan: plan,
        update_fertilization_plan_func=lambda plan: plan,
        create_planned_work_func=lambda work: work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=stub_run_clarification_loop,
        run_plan_proposal=stub_run_plan_proposal_cancelled,
    )

    result = await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"), "Tool should return cancelled when user declines")


@pytest.mark.asyncio
async def should_not_create_records_when_user_cancels(get_bonsai_by_name_func, list_fertilizers_func, tool_context):
    created_plans = []
    created_works = []

    tool = create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=lambda name: Fertilizer(id=1, name=name),
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        create_fertilization_plan_func=lambda plan: created_plans.append(plan) or plan,
        update_fertilization_plan_func=lambda plan: plan,
        create_planned_work_func=lambda work: created_works.append(work) or work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=stub_run_clarification_loop,
        run_plan_proposal=stub_run_plan_proposal_cancelled,
    )

    await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(created_plans, equal_to([]), "No plan should be created when user cancels")


@pytest.mark.asyncio
async def should_create_plan_and_planned_works_on_confirm(tool, tool_context, created_plans, created_works):
    result = await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"), "Tool should return success")
    assert_that(len(created_plans), equal_to(1), "Exactly one FertilizationPlan should be created")
    assert_that(len(created_works), equal_to(1), "One PlannedWork per entry should be created")


@pytest.mark.asyncio
async def should_link_planned_works_to_plan(tool, tool_context, created_plans, created_works):
    await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(created_works[0].plan_id, not_none(), "PlannedWork should have a plan_id linking to the plan")


@pytest.mark.asyncio
async def should_write_wiki_page_on_confirm(get_bonsai_by_name_func, list_fertilizers_func, tool_context):
    written_pages = {}

    tool = create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=lambda name: Fertilizer(id=1, name=name, recommended_amount="5g"),
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        create_fertilization_plan_func=lambda plan: _assign_id(plan, 42),
        update_fertilization_plan_func=lambda plan: plan,
        create_planned_work_func=lambda work: work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: written_pages.update({path: content}) or {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=stub_run_clarification_loop,
        run_plan_proposal=stub_run_plan_proposal,
    )

    await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(len(written_pages) >= 1, equal_to(True), "At least one wiki page should be written")


@pytest.mark.asyncio
async def should_abandon_existing_plan_when_creating_new_one(get_bonsai_by_name_func, list_fertilizers_func, tool_context):
    deleted_future_works_calls = []
    updated_plans = []
    existing_plan = FertilizationPlan(
        id=99, bonsai_id=1,
        period_start=date(2026, 1, 1), period_end=date(2026, 2, 28),
        status="active", wiki_path="bonsai/shikamaru/plans/2026-01_to_2026-02.md",
    )

    tool = create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=lambda name: Fertilizer(id=1, name=name),
        get_active_fertilization_plan_func=lambda bonsai_id: existing_plan,
        create_fertilization_plan_func=lambda plan: _assign_id(plan, 100),
        update_fertilization_plan_func=lambda plan: updated_plans.append(plan) or plan,
        create_planned_work_func=lambda work: work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: deleted_future_works_calls.append(plan_id) or 0,
        read_wiki_page_func=lambda path: {"status": "success", "content": "**Status:** active\nsome content"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=stub_run_clarification_loop,
        run_plan_proposal=stub_run_plan_proposal,
    )

    await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(deleted_future_works_calls, equal_to([99]), "Should delete future works of existing plan")
    assert_that(updated_plans[0].status, equal_to("abandoned"), "Existing plan should be marked abandoned")


@pytest.mark.asyncio
async def should_pass_bonsai_name_and_period_to_clarification_prompt(get_bonsai_by_name_func, list_fertilizers_func, tool_context):
    received_prompts = []

    async def capturing_clarification(rendered_prompt: str, outer_tool_context=None) -> dict:
        received_prompts.append(rendered_prompt)
        return {"objectives": "growth", "preferences": "Biogold", "context": "none"}

    tool = create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=lambda name: Fertilizer(id=1, name=name),
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        create_fertilization_plan_func=lambda plan: _assign_id(plan, 1),
        update_fertilization_plan_func=lambda plan: plan,
        create_planned_work_func=lambda work: work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=capturing_clarification,
        run_plan_proposal=stub_run_plan_proposal,
    )

    await tool(bonsai_name="Shikamaru", start_date="2026-03-01", end_date="2026-07-31", tool_context=tool_context)

    assert_that(received_prompts[0], contains_string("Shikamaru"), "Clarification prompt should include bonsai name")
    assert_that(received_prompts[0], contains_string("2026-03-01"), "Clarification prompt should include start date")


async def stub_run_clarification_loop(rendered_prompt: str, outer_tool_context=None) -> dict:
    return {"objectives": "active growth", "preferences": "Biogold", "context": "none"}


async def stub_run_plan_proposal(rendered_prompt: str, outer_tool_context=None) -> dict:
    return {
        "entries": [
            {"date": "2026-03-15", "fertilizer_name": "Biogold", "dose": "5g", "notes": "Spring boost"},
        ],
        "rationale": "Biogold in spring for nitrogen push",
    }


async def stub_run_plan_proposal_cancelled(rendered_prompt: str, outer_tool_context=None) -> dict:
    return {"cancelled": True, "reason": "user_cancelled"}


def _assign_id(plan, plan_id: int):
    plan.id = plan_id
    return plan


@pytest.fixture
def tool_context():
    return MockToolContext()


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Shikamaru", species_id=1)


@pytest.fixture
def existing_fertilizer():
    return Fertilizer(id=1, name="Biogold", recommended_amount="5g")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None
    return get_bonsai_by_name


@pytest.fixture
def list_fertilizers_func(existing_fertilizer):
    return lambda: [existing_fertilizer]


@pytest.fixture
def created_plans():
    return []


@pytest.fixture
def created_works():
    return []


@pytest.fixture
def tool(get_bonsai_by_name_func, list_fertilizers_func, created_plans, created_works):
    def create_fertilization_plan(plan):
        plan.id = 42
        created_plans.append(plan)
        return plan

    def create_planned_work(work: PlannedWork):
        created_works.append(work)
        return work

    return create_manage_fertilization_plan_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=list_fertilizers_func,
        get_fertilizer_by_name_func=lambda name: Fertilizer(id=1, name=name, recommended_amount="5g"),
        get_active_fertilization_plan_func=lambda bonsai_id: None,
        create_fertilization_plan_func=create_fertilization_plan,
        update_fertilization_plan_func=lambda plan: plan,
        create_planned_work_func=create_planned_work,
        delete_future_planned_works_func=lambda plan_id, cutoff_date: 0,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        list_wiki_files_func=lambda directory, pattern="*.md": [],
        run_clarification_loop=stub_run_clarification_loop,
        run_plan_proposal=stub_run_plan_proposal,
    )
