import pytest
from hamcrest import assert_that, equal_to, contains_string

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.cultivation.plan.fertilization.recommend_fertilizer import (
    create_recommend_fertilizer_tool,
)


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(tool):
    result = await tool(bonsai_name="Unknown")

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_no_fertilizers_available(get_bonsai_by_name_func):
    tool = create_recommend_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_fertilizers_func=lambda user_id=None: [],
        read_wiki_page_func=lambda path: {"status": "error", "message": "page_not_found"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        run_recommendation=stub_run_recommendation,
    )

    result = await tool(bonsai_name="Shikamaru")

    assert_that(result, equal_to({"status": "error", "message": "no_fertilizers_available"}),
        "Empty fertilizer catalog should return no_fertilizers_available error")


@pytest.mark.asyncio
async def should_write_wiki_page_after_recommendation(get_bonsai_by_name_func, list_fertilizers_func, list_bonsai_events_func, read_wiki_page_func):
    written_pages = {}

    def write_wiki_page(path, content):
        written_pages[path] = content
        return {"status": "success"}

    tool = create_recommend_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_fertilizers_func=list_fertilizers_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page,
        run_recommendation=stub_run_recommendation,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that("users/default/bonsai/shikamaru/fertilization-plan.md" in written_pages, equal_to(True),
        "Wiki page should be written at users/<user_id>/bonsai/<slug>/fertilization-plan.md")
    assert_that(written_pages["users/default/bonsai/shikamaru/fertilization-plan.md"],
        contains_string("Plan activo"), "Written wiki content should contain the plan")


@pytest.mark.asyncio
async def should_return_fertilizer_name_and_reasoning_on_success(tool):
    result = await tool(bonsai_name="Shikamaru")

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when recommendation succeeds")
    assert_that(result["fertilizer_name"], equal_to("Biogold"),
        "Tool should return the fertilizer name from the recommendation")
    assert_that(result["reasoning"], equal_to("Best choice for deciduous trees"),
        "Tool should return the reasoning from the recommendation")


@pytest.mark.asyncio
async def should_include_bonsai_events_in_context(get_bonsai_by_name_func, list_fertilizers_func, read_wiki_page_func, write_wiki_page_func):
    received_contexts = []

    async def capturing_runner(context):
        received_contexts.append(context)
        return {"fertilizer_name": "Biogold", "reasoning": "ok", "wiki_content": "# Plan\n"}

    list_events = lambda bonsai_id: [{"event_type": "fertilization", "details": "Biogold applied"}]

    tool = create_recommend_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_events,
        list_fertilizers_func=list_fertilizers_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=capturing_runner,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that(received_contexts[0], contains_string("fertilization"),
        "Context passed to LLM runner should include bonsai event history")


@pytest.mark.asyncio
async def should_include_current_date_in_context(get_bonsai_by_name_func, list_fertilizers_func, list_bonsai_events_func, read_wiki_page_func, write_wiki_page_func):
    received_contexts = []

    async def capturing_runner(context):
        received_contexts.append(context)
        return {"fertilizer_name": "Biogold", "reasoning": "ok", "wiki_content": "# Plan\n"}

    tool = create_recommend_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_fertilizers_func=list_fertilizers_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=capturing_runner,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that(received_contexts[0], contains_string("Fecha actual:"),
        "Context passed to LLM runner should include the current date for seasonal reasoning")


@pytest.mark.asyncio
async def should_include_existing_wiki_plan_in_context(get_bonsai_by_name_func, list_fertilizers_func, list_bonsai_events_func, write_wiki_page_func):
    received_contexts = []

    async def capturing_runner(context):
        received_contexts.append(context)
        return {"fertilizer_name": "Biogold", "reasoning": "ok", "wiki_content": "# Plan\n"}

    def read_wiki_page(path):
        if path == "users/default/bonsai/shikamaru/fertilization-plan.md":
            return {"status": "success", "content": "# Plan anterior\n## Plan activo\nBiogold"}
        return {"status": "error", "message": "page_not_found"}

    tool = create_recommend_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_fertilizers_func=list_fertilizers_func,
        read_wiki_page_func=read_wiki_page,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=capturing_runner,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that(received_contexts[0], contains_string("Plan anterior"),
        "Context passed to LLM runner should include the existing wiki plan")


async def stub_run_recommendation(context: str) -> dict:
    return {
        "fertilizer_name": "Biogold",
        "reasoning": "Best choice for deciduous trees",
        "wiki_content": "# Plan de fertilización\n\n## Plan activo\nBiogold\n\n## Historial\n",
    }


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Shikamaru", species_id=1)


@pytest.fixture
def existing_fertilizer():
    return Fertilizer(id=1, name="Biogold", recommended_amount="5g")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str, user_id=None) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None
    return get_bonsai_by_name


@pytest.fixture
def list_fertilizers_func(existing_fertilizer):
    return lambda user_id=None: [existing_fertilizer]


@pytest.fixture
def list_bonsai_events_func():
    return lambda bonsai_id: []


@pytest.fixture
def read_wiki_page_func():
    return lambda path: {"status": "error", "message": "page_not_found"}


@pytest.fixture
def write_wiki_page_func():
    return lambda path, content: {"status": "success"}


@pytest.fixture
def tool(get_bonsai_by_name_func, list_fertilizers_func, list_bonsai_events_func, read_wiki_page_func, write_wiki_page_func):
    return create_recommend_fertilizer_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_fertilizers_func=list_fertilizers_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=stub_run_recommendation,
    )
