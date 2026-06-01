import pytest
from hamcrest import assert_that, equal_to, contains_string

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.cultivation.plan.phytosanitary.recommend_phytosanitary import (
    create_recommend_phytosanitary_tool,
)


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(tool):
    result = await tool(bonsai_name="Unknown")

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_no_products_available(get_bonsai_by_name_func):
    tool = create_recommend_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=lambda bonsai_id: [],
        list_phytosanitary_func=lambda: [],
        read_wiki_page_func=lambda path: {"status": "error", "message": "page_not_found"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        run_recommendation=stub_run_recommendation,
    )

    result = await tool(bonsai_name="Shikamaru")

    assert_that(result, equal_to({"status": "error", "message": "no_products_available"}),
        "Empty phytosanitary catalog should return no_products_available error")


@pytest.mark.asyncio
async def should_write_wiki_page_after_recommendation(get_bonsai_by_name_func, list_phytosanitary_func, list_bonsai_events_func, read_wiki_page_func):
    written_pages = {}

    def write_wiki_page(path, content):
        written_pages[path] = content
        return {"status": "success"}

    tool = create_recommend_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_phytosanitary_func=list_phytosanitary_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page,
        run_recommendation=stub_run_recommendation,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that("bonsai/shikamaru/phytosanitary-plan.md" in written_pages, equal_to(True),
        "Wiki page should be written at bonsai/<slug>/phytosanitary-plan.md")
    assert_that(written_pages["bonsai/shikamaru/phytosanitary-plan.md"],
        contains_string("Plan activo"), "Written wiki content should contain the plan")


@pytest.mark.asyncio
async def should_return_treatments_list_and_reasoning_on_success(tool):
    result = await tool(bonsai_name="Shikamaru")

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when recommendation succeeds")
    assert_that(result["treatments"], equal_to([{"phytosanitary_name": "Aceite de Neem", "purpose": "Control de ácaros"}]),
        "Tool should return the treatments list from the recommendation")
    assert_that(result["reasoning"], equal_to("Effective against spider mites"),
        "Tool should return the reasoning from the recommendation")


@pytest.mark.asyncio
async def should_include_current_date_in_context(get_bonsai_by_name_func, list_phytosanitary_func, list_bonsai_events_func, read_wiki_page_func, write_wiki_page_func):
    received_contexts = []

    async def capturing_runner(context):
        received_contexts.append(context)
        return {"treatments": [{"phytosanitary_name": "Aceite de Neem", "purpose": "ácaros"}], "reasoning": "ok", "wiki_content": "# Plan\n"}

    tool = create_recommend_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_phytosanitary_func=list_phytosanitary_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=capturing_runner,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that(received_contexts[0], contains_string("Fecha actual:"),
        "Context passed to LLM runner should include the current date for seasonal reasoning")


@pytest.mark.asyncio
async def should_include_bonsai_events_in_context(get_bonsai_by_name_func, list_phytosanitary_func, read_wiki_page_func, write_wiki_page_func):
    received_contexts = []

    async def capturing_runner(context):
        received_contexts.append(context)
        return {"treatments": [{"phytosanitary_name": "Aceite de Neem", "purpose": "ácaros"}], "reasoning": "ok", "wiki_content": "# Plan\n"}

    list_events = lambda bonsai_id: [{"event_type": "phytosanitary", "details": "spider mites detected"}]

    tool = create_recommend_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_events,
        list_phytosanitary_func=list_phytosanitary_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=capturing_runner,
    )

    await tool(bonsai_name="Shikamaru")

    assert_that(received_contexts[0], contains_string("spider mites"),
        "Context passed to LLM runner should include bonsai event history")


async def stub_run_recommendation(context: str) -> dict:
    return {
        "treatments": [{"phytosanitary_name": "Aceite de Neem", "purpose": "Control de ácaros"}],
        "reasoning": "Effective against spider mites",
        "wiki_content": "# Plan fitosanitario\n\n## Plan activo\nAceite de Neem\n\n## Historial\n",
    }


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Shikamaru", species_id=1)


@pytest.fixture
def existing_product():
    return Phytosanitary(id=1, name="Aceite de Neem")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None
    return get_bonsai_by_name


@pytest.fixture
def list_phytosanitary_func(existing_product):
    return lambda: [existing_product]


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
def tool(get_bonsai_by_name_func, list_phytosanitary_func, list_bonsai_events_func, read_wiki_page_func, write_wiki_page_func):
    return create_recommend_phytosanitary_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_phytosanitary_func=list_phytosanitary_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=stub_run_recommendation,
    )
