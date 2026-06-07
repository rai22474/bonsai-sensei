from datetime import date

import pytest
from hamcrest import assert_that, equal_to, has_key, contains_string

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.garden.kantei.analyze_bonsai_photo import create_analyze_bonsai_photo_tool


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_for_invalid_analysis_type(analyze_tool, tool_context):
    result = await analyze_tool("Olmo", "invalid_type", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "invalid_analysis_type"}),
        "Invalid analysis type should return invalid_analysis_type error")


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(analyze_tool, tool_context):
    result = await analyze_tool("Unknown", "health", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_no_photos_when_bonsai_has_no_photos(analyze_tool_no_photos, tool_context):
    result = await analyze_tool_no_photos("Olmo", "health", tool_context=tool_context)

    assert_that(result, equal_to({"status": "no_photos", "bonsai_name": "Olmo"}),
        "Bonsai with no photos should return no_photos status")


@pytest.mark.asyncio
async def should_return_error_when_photo_file_not_found(analyze_tool_missing_file, tool_context):
    result = await analyze_tool_missing_file("Olmo", "health", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "photo_file_not_found"}),
        "Missing photo file should return photo_file_not_found error")


@pytest.mark.asyncio
async def should_return_analysis_complete_with_correct_fields(analyze_tool, tool_context):
    result = await analyze_tool("Olmo", "health", tool_context=tool_context)

    assert_that(result["status"], equal_to("analysis_complete"),
        "Result status should be analysis_complete")
    assert_that(result["bonsai_name"], equal_to("Olmo"),
        "Result should include bonsai_name")
    assert_that(result["analysis_type"], equal_to("health"),
        "Result should include analysis_type")
    assert_that(result, has_key("analysis"), "Result should include analysis")


@pytest.mark.asyncio
async def should_use_latest_photo_when_no_date_hint(tool_context, existing_bonsai):
    photos = [
        BonsaiPhoto(id=1, bonsai_id=1, file_path="photo_jan.jpg", taken_on=date(2025, 1, 10)),
        BonsaiPhoto(id=2, bonsai_id=1, file_path="photo_jun.jpg", taken_on=date(2025, 6, 20)),
    ]
    used_paths = []

    async def run_photo_analysis(photo_bytes, analysis_type):
        return "analysis result"

    async def noop_update_index(bonsai_name, user_id=None):
        pass

    tool = create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name, user_id=None: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: photos if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: used_paths.append(path) or b"bytes",
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=lambda path, content: None,
        update_reports_index_func=noop_update_index,
    )

    await tool("Olmo", "health", date_hint="", tool_context=tool_context)

    assert_that(used_paths[0], equal_to("photo_jun.jpg"),
        "Latest photo should be selected when no date hint provided")


@pytest.mark.asyncio
async def should_select_photo_by_month_hint(tool_context, existing_bonsai):
    photos = [
        BonsaiPhoto(id=1, bonsai_id=1, file_path="photo_jan.jpg", taken_on=date(2025, 1, 10)),
        BonsaiPhoto(id=2, bonsai_id=1, file_path="photo_mar.jpg", taken_on=date(2025, 3, 20)),
    ]
    used_paths = []

    async def run_photo_analysis(photo_bytes, analysis_type):
        return "analysis result"

    async def noop_update_index(bonsai_name, user_id=None):
        pass

    tool = create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name, user_id=None: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: photos if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: used_paths.append(path) or b"bytes",
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=lambda path, content: None,
        update_reports_index_func=noop_update_index,
    )

    await tool("Olmo", "health", date_hint="marzo", tool_context=tool_context)

    assert_that(used_paths[0], equal_to("photo_mar.jpg"),
        "Photo from March should be selected when 'marzo' date_hint is provided")


@pytest.mark.asyncio
async def should_record_taken_on_in_tool_context_state(analyze_tool, tool_context):
    await analyze_tool("Olmo", "health", tool_context=tool_context)

    assert_that(
        tool_context.state["photos_for_analysis_taken_on"],
        equal_to(["2025-03-15"]),
        "Tool should record taken_on date in tool_context state",
    )


@pytest.mark.asyncio
async def should_save_wiki_report_with_wikilink_after_analysis(tool_context, existing_bonsai, existing_photo):
    written_pages = {}

    async def update_reports_index(bonsai_name, user_id=None):
        pass

    tool = _make_tool_with_captures(
        existing_bonsai=existing_bonsai,
        existing_photo=existing_photo,
        written_pages=written_pages,
        update_reports_index=update_reports_index,
    )

    await tool("Olmo", "health", tool_context=tool_context)

    assert_that(
        written_pages.get("users/default/bonsai/olmo/reports/2025-03-15-health.md", ""),
        contains_string("[[bonsai/olmo/photo1.jpg|Ver foto]]"),
        "Report should contain wikilink to the analysed photo",
    )


@pytest.mark.asyncio
async def should_update_reports_index_after_analysis(tool_context, existing_bonsai, existing_photo):
    index_calls = []

    async def update_reports_index(bonsai_name, user_id=None):
        index_calls.append(bonsai_name)

    tool = _make_tool_with_captures(
        existing_bonsai=existing_bonsai,
        existing_photo=existing_photo,
        update_reports_index=update_reports_index,
    )

    await tool("Olmo", "health", tool_context=tool_context)

    assert_that(index_calls, equal_to(["Olmo"]),
        "Reports index should be updated with the bonsai name after analysis")


@pytest.mark.asyncio
async def should_not_save_report_when_bonsai_not_found(tool_context, existing_bonsai, existing_photo):
    written_pages = {}

    async def update_reports_index(bonsai_name, user_id=None):
        pass

    tool = _make_tool_with_captures(
        existing_bonsai=existing_bonsai,
        existing_photo=existing_photo,
        written_pages=written_pages,
        update_reports_index=update_reports_index,
        get_bonsai_by_name_func=lambda name, user_id=None: None,
    )

    await tool("Unknown", "health", tool_context=tool_context)

    assert_that(written_pages, equal_to({}),
        "No report should be saved when bonsai is not found")


def _make_tool_with_captures(
    existing_bonsai,
    existing_photo,
    written_pages=None,
    update_reports_index=None,
    get_bonsai_by_name_func=None,
):
    pages = written_pages if written_pages is not None else {}

    async def _noop_update_index(bonsai_name, user_id=None):
        pass

    async def run_photo_analysis(photo_bytes, analysis_type):
        return "analysis result"

    return create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func or (lambda name, user_id=None: existing_bonsai if name == existing_bonsai.name else None),
        list_bonsai_photos_func=lambda bonsai_id: [existing_photo] if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: b"photo_bytes",
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=lambda path, content: pages.update({path: content}),
        update_reports_index_func=update_reports_index or _noop_update_index,
    )


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Olmo", species_id=1)


@pytest.fixture
def existing_photo():
    return BonsaiPhoto(id=1, bonsai_id=1, file_path="bonsai/olmo/photo1.jpg", taken_on=date(2025, 3, 15))


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def analyze_tool(existing_bonsai, existing_photo):
    async def run_photo_analysis(photo_bytes, analysis_type):
        return "detailed analysis text"

    async def noop_update_index(bonsai_name, user_id=None):
        pass

    return create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name, user_id=None: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [existing_photo] if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: b"photo_bytes",
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=lambda path, content: None,
        update_reports_index_func=noop_update_index,
    )


@pytest.fixture
def analyze_tool_no_photos(existing_bonsai):
    async def run_photo_analysis(photo_bytes, analysis_type):
        return "detailed analysis text"

    async def noop_update_index(bonsai_name, user_id=None):
        pass

    return create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name, user_id=None: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [],
        load_photo_bytes=lambda path: b"photo_bytes",
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=lambda path, content: None,
        update_reports_index_func=noop_update_index,
    )


@pytest.fixture
def analyze_tool_missing_file(existing_bonsai, existing_photo):
    async def run_photo_analysis(photo_bytes, analysis_type):
        return "detailed analysis text"

    async def noop_update_index(bonsai_name, user_id=None):
        pass

    return create_analyze_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name, user_id=None: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [existing_photo] if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: None,
        run_photo_analysis=run_photo_analysis,
        write_wiki_page_func=lambda path, content: None,
        update_reports_index_func=noop_update_index,
    )
