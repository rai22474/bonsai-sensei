from datetime import date

import pytest
from hamcrest import assert_that, contains_string, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.development_plan import DevelopmentPlan
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.refinement.write_work_notes import (
    create_write_work_analysis_tool,
    create_write_work_result_tool,
)


class MockToolContext:
    def __init__(self, user_id="user-123"):
        self.user_id = user_id
        self.state = {}


# --- write_work_analysis ---

@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found_for_analysis(analysis_tool, tool_context):
    result = await analysis_tool(bonsai_name="Unknown", work_type="mekiri", notes="notas", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_write_analysis_under_refinements_subdir(analysis_tool, tool_context):
    result = await analysis_tool(bonsai_name="Naruto", work_type="mekiri", notes="Cortar brotes apicales", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"), "Should return success")
    assert_that(result["wiki_path"], contains_string("/refinements/mekiri-"),
        "Analysis wiki_path should be under refinements/")


@pytest.mark.asyncio
async def should_use_plan_directory_for_analysis_when_work_linked_to_plan(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    today = date.today().isoformat()
    plan = _make_plan("users/user-42/bonsai/naruto/design-plans/2026-06_to_2027-05.md")
    works = [PlannedWork(id=1, bonsai_id=1, work_type="mekiri", payload={}, scheduled_date=date(2026, 6, 15), development_plan_id=10)]

    tool = create_write_work_analysis_tool(
        run_wiki_generator=_stub_wiki_generator("# Análisis"),
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: works,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
        get_development_plan_func=lambda plan_id: plan,
    )

    result = await tool(bonsai_name="Naruto", work_type="mekiri", notes="Notas", tool_context=tool_context)

    expected = f"users/user-42/bonsai/naruto/design-plans/2026-06_to_2027-05/refinements/mekiri-{today}.md"
    assert_that(result["wiki_path"], equal_to(expected),
        "Analysis should be nested under plan dir/refinements")


# --- write_work_result ---

@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found_for_result(result_tool, tool_context):
    result = await result_tool(bonsai_name="Unknown", work_type="poda", notes="notas", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_write_result_under_results_subdir(result_tool, tool_context):
    result = await result_tool(bonsai_name="Naruto", work_type="poda", notes="Poda completada", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"), "Should return success")
    assert_that(result["wiki_path"], contains_string("/results/poda-"),
        "Result wiki_path should be under results/")


@pytest.mark.asyncio
async def should_use_plan_directory_for_result_when_work_linked_to_plan(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    today = date.today().isoformat()
    plan = _make_plan("users/user-42/bonsai/naruto/design-plans/2026-06_to_2027-05.md")
    works = [PlannedWork(id=2, bonsai_id=1, work_type="poda", payload={}, scheduled_date=date(2026, 9, 1), development_plan_id=10)]

    tool = create_write_work_result_tool(
        run_wiki_generator=_stub_wiki_generator("# Resultado"),
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: works,
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
        get_development_plan_func=lambda plan_id: plan,
    )

    result = await tool(bonsai_name="Naruto", work_type="poda", notes="Notas", tool_context=tool_context)

    expected = f"users/user-42/bonsai/naruto/design-plans/2026-06_to_2027-05/results/poda-{today}.md"
    assert_that(result["wiki_path"], equal_to(expected),
        "Result should be nested under plan dir/results")


@pytest.mark.asyncio
async def should_pass_photo_analyses_to_result_generator(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    captured_prompts = []

    async def capturing_generator(message):
        captured_prompts.append(message.parts[0].text)
        yield _make_text_event("# Resultado")

    tool = create_write_work_result_tool(
        run_wiki_generator=capturing_generator,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
    )

    await result_tool_call(tool, tool_context, photo_analyses=["Ramas bien equilibradas tras la poda"])

    assert_that(len(captured_prompts), equal_to(1), "Generator should be called once")
    assert_that(captured_prompts[0], contains_string("Ramas bien equilibradas"),
        "Photo analysis should be included in the generator prompt")


@pytest.mark.asyncio
async def should_update_refinement_wiki_path_on_matching_work(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    updated = {}
    work = PlannedWork(id=5, bonsai_id=1, work_type="mekiri", payload={}, scheduled_date=date(2026, 9, 1))

    tool = create_write_work_analysis_tool(
        run_wiki_generator=_stub_wiki_generator("# Análisis"),
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [work],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
        update_refinement_wiki_path_func=lambda work_id, wiki_path: updated.update({"work_id": work_id, "wiki_path": wiki_path}),
    )

    result = await tool(bonsai_name="Naruto", work_type="mekiri", notes="Notas", tool_context=tool_context)

    assert_that(updated.get("work_id"), equal_to(5), "Should update the primary matching work")
    assert_that(updated.get("wiki_path"), equal_to(result["wiki_path"]), "Should store the written wiki_path")


@pytest.mark.asyncio
async def should_analyze_recent_bonsai_photos_and_include_in_wiki(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    captured_prompts = []
    today = date.today()
    photo = BonsaiPhoto(id=1, bonsai_id=1, file_path="naruto/photo.webp", taken_on=today)

    async def capturing_generator(message):
        captured_prompts.append(message.parts[0].text)
        yield _make_text_event("# Resultado")

    tool = create_write_work_result_tool(
        run_wiki_generator=capturing_generator,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
        list_bonsai_photos_func=lambda bonsai_id: [photo],
        read_photo_bytes_func=lambda file_path: b"fake_photo_bytes",
        run_photo_analysis_func=_async_photo_analysis("Ramas bien distribuidas tras la poda"),
    )

    await tool(bonsai_name="Naruto", work_type="poda", notes="Poda realizada", tool_context=tool_context)

    assert_that(len(captured_prompts), equal_to(1), "Generator should be called once")
    assert_that(captured_prompts[0], contains_string("Ramas bien distribuidas"),
        "Gallery photo analysis should be included in the generator prompt")


@pytest.mark.asyncio
async def should_skip_photos_older_than_today(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    captured_prompts = []
    yesterday_photo = BonsaiPhoto(id=2, bonsai_id=1, file_path="naruto/old.webp", taken_on=date(2026, 1, 1))

    async def capturing_generator(message):
        captured_prompts.append(message.parts[0].text)
        yield _make_text_event("# Resultado")

    tool = create_write_work_result_tool(
        run_wiki_generator=capturing_generator,
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
        list_bonsai_photos_func=lambda bonsai_id: [yesterday_photo],
        read_photo_bytes_func=lambda file_path: b"fake_bytes",
        run_photo_analysis_func=_async_photo_analysis("should not appear"),
    )

    await tool(bonsai_name="Naruto", work_type="poda", notes="Poda realizada", tool_context=tool_context)

    assert_that(captured_prompts[0], contains_string("should not appear") is False or True,
        "Old photos should not be analyzed")
    assert_that("should not appear" not in captured_prompts[0], equal_to(True),
        "Photos older than today should not be analyzed")


@pytest.mark.asyncio
async def should_link_recent_photos_when_writing_result(tool_context, get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    linked = {}
    work = PlannedWork(id=7, bonsai_id=1, work_type="poda", payload={}, scheduled_date=date(2026, 9, 20))

    tool = create_write_work_result_tool(
        run_wiki_generator=_stub_wiki_generator("# Resultado"),
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [work],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
        link_recent_photos_func=lambda bonsai_id, planned_work_id: linked.update({"bonsai_id": bonsai_id, "work_id": planned_work_id}),
    )

    await tool(bonsai_name="Naruto", work_type="poda", notes="Poda completada", tool_context=tool_context)

    assert_that(linked.get("bonsai_id"), equal_to(1), "Should link photos for the correct bonsai")
    assert_that(linked.get("work_id"), equal_to(7), "Should link photos to the primary matching work")


async def result_tool_call(tool, tool_context, photo_analyses=None):
    return await tool(
        bonsai_name="Naruto",
        work_type="poda",
        notes="Poda completada con éxito",
        photo_analyses=photo_analyses,
        tool_context=tool_context,
    )


def _make_plan(wiki_path: str) -> DevelopmentPlan:
    return DevelopmentPlan(
        id=10,
        bonsai_id=1,
        development_path="planton",
        current_phase="engorde",
        target_style="moyogi",
        design_goal="trunk thickening",
        period_start=date(2026, 6, 1),
        period_end=date(2027, 5, 31),
        status="active",
        wiki_path=wiki_path,
    )


def _async_photo_analysis(result: str):
    async def analyze(photo_bytes, analysis_type):
        return result
    return analyze


def _stub_wiki_generator(content: str):
    async def run(message):
        yield _make_text_event(content)
    return run


def _make_text_event(text: str):
    from google.adk.events import Event
    from google.genai import types
    return Event(content=types.Content(role="model", parts=[types.Part(text=text)]))


@pytest.fixture
def tool_context():
    return MockToolContext()


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Naruto", species_id=1, user_id="user-42")


@pytest.fixture
def get_bonsai_by_name_func(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None
    return get_bonsai_by_name


@pytest.fixture
def ask_human_func():
    async def ask_human(question, tool_context=None):
        return "Naruto"
    return ask_human


@pytest.fixture
def build_bonsai_name_question_func():
    return lambda: "¿Para qué bonsái?"


@pytest.fixture
def analysis_tool(get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    return create_write_work_analysis_tool(
        run_wiki_generator=_stub_wiki_generator("# Análisis de mekiri"),
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
    )


@pytest.fixture
def result_tool(get_bonsai_by_name_func, ask_human_func, build_bonsai_name_question_func):
    return create_write_work_result_tool(
        run_wiki_generator=_stub_wiki_generator("# Resultado de poda"),
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_planned_works_func=lambda bonsai_id: [],
        read_wiki_page_func=lambda path: {"status": "error"},
        write_wiki_page_func=lambda path, content: {"status": "success"},
        ask_human=ask_human_func,
        build_bonsai_name_question=build_bonsai_name_question_func,
    )
