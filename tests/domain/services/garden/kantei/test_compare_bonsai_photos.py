from datetime import date

import pytest
from hamcrest import assert_that, equal_to, less_than

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.garden.kantei.compare_bonsai_photos import create_compare_bonsai_photos_tool


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(compare_tool, tool_context):
    result = await compare_tool("Unknown", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_no_photos_when_bonsai_has_no_photos(compare_tool_no_photos, tool_context):
    result = await compare_tool_no_photos("Olmo", tool_context=tool_context)

    assert_that(result, equal_to({"status": "no_photos", "bonsai_name": "Olmo"}),
        "Bonsai with no photos should return no_photos status")


@pytest.mark.asyncio
async def should_return_only_one_photo_when_single_photo_exists(compare_tool_one_photo, tool_context):
    result = await compare_tool_one_photo("Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("only_one_photo"),
        "Bonsai with one photo should return only_one_photo status")


@pytest.mark.asyncio
async def should_return_error_when_older_photo_file_not_found(tool_context, existing_bonsai, two_photos):
    load_call_count = [0]

    def load_photo_bytes_first_missing(path):
        load_call_count[0] += 1
        return None if load_call_count[0] == 1 else b"bytes"

    async def run_photo_comparison(older_bytes, newer_bytes, intent):
        return "comparison result"

    tool = create_compare_bonsai_photos_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: two_photos if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=load_photo_bytes_first_missing,
        run_photo_comparison=run_photo_comparison,
    )

    result = await tool("Olmo", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "photo_file_not_found"}),
        "Missing older photo file should return photo_file_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_newer_photo_file_not_found(tool_context, existing_bonsai, two_photos):
    load_call_count = [0]

    def load_photo_bytes_second_missing(path):
        load_call_count[0] += 1
        return b"bytes" if load_call_count[0] == 1 else None

    async def run_photo_comparison(older_bytes, newer_bytes, intent):
        return "comparison result"

    tool = create_compare_bonsai_photos_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: two_photos if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=load_photo_bytes_second_missing,
        run_photo_comparison=run_photo_comparison,
    )

    result = await tool("Olmo", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "photo_file_not_found"}),
        "Missing newer photo file should return photo_file_not_found error")


@pytest.mark.asyncio
async def should_return_comparison_complete_with_correct_fields(compare_tool, tool_context):
    result = await compare_tool("Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("comparison_complete"),
        "Result status should be comparison_complete")
    assert_that(result["bonsai_name"], equal_to("Olmo"),
        "Result should include bonsai_name")
    assert_that("older_taken_on" in result, equal_to(True), "Result should include older_taken_on")
    assert_that("newer_taken_on" in result, equal_to(True), "Result should include newer_taken_on")
    assert_that("comparison" in result, equal_to(True), "Result should include comparison")


@pytest.mark.asyncio
async def should_compare_oldest_and_newest_photos(compare_tool, tool_context):
    result = await compare_tool("Olmo", tool_context=tool_context)

    older_date = date.fromisoformat(result["older_taken_on"])
    newer_date = date.fromisoformat(result["newer_taken_on"])

    assert_that(older_date, less_than(newer_date), "Older photo date should be before newer photo date")


@pytest.mark.asyncio
async def should_record_both_taken_on_in_tool_context_state(compare_tool, tool_context):
    await compare_tool("Olmo", tool_context=tool_context)

    assert_that(
        len(tool_context.state["photos_for_analysis_taken_on"]),
        equal_to(2),
        "Tool should record both taken_on dates in tool_context state",
    )


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Olmo", species_id=1)


@pytest.fixture
def two_photos():
    return [
        BonsaiPhoto(id=1, bonsai_id=1, file_path="photo_jan.jpg", taken_on=date(2025, 1, 10)),
        BonsaiPhoto(id=2, bonsai_id=1, file_path="photo_jun.jpg", taken_on=date(2025, 6, 20)),
    ]


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def compare_tool(existing_bonsai, two_photos):
    async def run_photo_comparison(older_bytes, newer_bytes, intent):
        return "visual comparison result"

    return create_compare_bonsai_photos_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: two_photos if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: b"photo_bytes",
        run_photo_comparison=run_photo_comparison,
    )


@pytest.fixture
def compare_tool_no_photos(existing_bonsai):
    async def run_photo_comparison(older_bytes, newer_bytes, intent):
        return "visual comparison result"

    return create_compare_bonsai_photos_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [],
        load_photo_bytes=lambda path: b"photo_bytes",
        run_photo_comparison=run_photo_comparison,
    )


@pytest.fixture
def compare_tool_one_photo(existing_bonsai):
    single_photo = BonsaiPhoto(id=1, bonsai_id=1, file_path="photo.jpg", taken_on=date(2025, 3, 15))

    async def run_photo_comparison(older_bytes, newer_bytes, intent):
        return "visual comparison result"

    return create_compare_bonsai_photos_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [single_photo] if bonsai_id == existing_bonsai.id else [],
        load_photo_bytes=lambda path: b"photo_bytes",
        run_photo_comparison=run_photo_comparison,
    )
