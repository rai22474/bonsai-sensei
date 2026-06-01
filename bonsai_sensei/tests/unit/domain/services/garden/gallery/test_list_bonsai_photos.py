from datetime import date

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.garden.gallery.list_bonsai_photos import (
    create_list_bonsai_photos_tool,
    create_show_bonsai_photos_tool,
)


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found_list(list_bonsai_photos_tool_no_bonsai):
    result = await list_bonsai_photos_tool_no_bonsai("Unknown")

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_empty_list_when_no_photos(list_bonsai_photos_tool_empty):
    result = await list_bonsai_photos_tool_empty("Olmo")

    assert_that(result, equal_to({"status": "success", "photos": []}),
        "Bonsai with no photos should return empty list")


@pytest.mark.asyncio
async def should_return_photos_with_metadata(list_bonsai_photos_tool):
    result = await list_bonsai_photos_tool("Olmo")

    assert_that(result, equal_to({
        "status": "success",
        "photos": [{"id": 1, "file_path": "bonsai/olmo/photo1.jpg", "taken_on": "2025-03-15"}],
    }), "Photos should include id, file_path, and taken_on")


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found_show(show_bonsai_photos_tool_no_bonsai):
    result = await show_bonsai_photos_tool_no_bonsai("Unknown")

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_set_photos_to_display_in_tool_context_state(show_bonsai_photos_tool, tool_context):
    await show_bonsai_photos_tool("Olmo", tool_context=tool_context)

    assert_that(tool_context.state["photos_to_display"], equal_to(["bonsai/olmo/photo1.jpg"]),
        "Tool should set photos_to_display in tool_context state")


@pytest.mark.asyncio
async def should_return_photos_with_metadata_show(show_bonsai_photos_tool):
    result = await show_bonsai_photos_tool("Olmo")

    assert_that(result, equal_to({
        "status": "success",
        "photos": [{"id": 1, "file_path": "bonsai/olmo/photo1.jpg", "taken_on": "2025-03-15"}],
    }), "Photos should include id, file_path, and taken_on")


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
def list_bonsai_photos_tool(existing_bonsai, existing_photo):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    def list_bonsai_photos_func(bonsai_id: int) -> list[BonsaiPhoto]:
        return [existing_photo] if bonsai_id == existing_bonsai.id else []

    return create_list_bonsai_photos_tool(get_bonsai_by_name, list_bonsai_photos_func)


@pytest.fixture
def list_bonsai_photos_tool_empty(existing_bonsai):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    def list_bonsai_photos_func(bonsai_id: int) -> list[BonsaiPhoto]:
        return []

    return create_list_bonsai_photos_tool(get_bonsai_by_name, list_bonsai_photos_func)


@pytest.fixture
def list_bonsai_photos_tool_no_bonsai():
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return None

    def list_bonsai_photos_func(bonsai_id: int) -> list[BonsaiPhoto]:
        return []

    return create_list_bonsai_photos_tool(get_bonsai_by_name, list_bonsai_photos_func)


@pytest.fixture
def show_bonsai_photos_tool(existing_bonsai, existing_photo):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return existing_bonsai if name == existing_bonsai.name else None

    def list_bonsai_photos_func(bonsai_id: int) -> list[BonsaiPhoto]:
        return [existing_photo] if bonsai_id == existing_bonsai.id else []

    return create_show_bonsai_photos_tool(get_bonsai_by_name, list_bonsai_photos_func)


@pytest.fixture
def show_bonsai_photos_tool_no_bonsai():
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return None

    def list_bonsai_photos_func(bonsai_id: int) -> list[BonsaiPhoto]:
        return []

    return create_show_bonsai_photos_tool(get_bonsai_by_name, list_bonsai_photos_func)
