import pytest
from datetime import date
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.garden.analyze_bonsai_photo import create_analyze_bonsai_photo_tool


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(analyze_photo_tool):
    result = await analyze_photo_tool(bonsai_name="Unknown", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error",
    )


@pytest.mark.asyncio
async def should_return_no_photos_when_bonsai_has_no_photos(analyze_photo_tool_no_photos):
    result = await analyze_photo_tool_no_photos(bonsai_name="Olmo 1", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "no_photos", "bonsai_name": "Olmo 1"}),
        "Bonsai with no photos should return no_photos status",
    )


@pytest.mark.asyncio
async def should_return_error_when_photo_file_not_found(analyze_photo_tool_missing_file):
    result = await analyze_photo_tool_missing_file(bonsai_name="Olmo 1", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "photo_file_not_found"}),
        "Missing photo file should return photo_file_not_found error",
    )


@pytest.mark.asyncio
async def should_return_photo_ready_when_photo_exists(analyze_photo_tool):
    result = await analyze_photo_tool(bonsai_name="Olmo 1", tool_context=None)

    assert_that(
        result,
        equal_to({"status": "photo_ready", "bonsai_name": "Olmo 1", "taken_on": "2025-06-25"}),
        "Valid photo should return photo_ready status with metadata",
    )


@pytest.mark.asyncio
async def should_store_photo_bytes_in_tool_context(analyze_photo_tool):
    tool_context = FakeToolContext()

    await analyze_photo_tool(bonsai_name="Olmo 1", tool_context=tool_context)

    assert_that(
        tool_context.state.get("photo_for_analysis"),
        equal_to(b"fake_photo_bytes"),
        "Photo bytes should be stored in tool_context state",
    )


@pytest.fixture
def bonsai_item():
    return Bonsai(id=1, name="Olmo 1", species_id=1)


@pytest.fixture
def photo_item():
    return BonsaiPhoto(id=1, bonsai_id=1, file_path="olmo_1/2025-06-25.webp", taken_on=date(2025, 6, 25))


@pytest.fixture
def analyze_photo_tool(bonsai_item, photo_item):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return bonsai_item if name == bonsai_item.name else None

    def list_bonsai_photos(bonsai_id: int) -> list:
        return [photo_item] if bonsai_id == bonsai_item.id else []

    def load_photo_bytes(file_path: str) -> bytes | None:
        return b"fake_photo_bytes"

    return create_analyze_bonsai_photo_tool(get_bonsai_by_name, list_bonsai_photos, load_photo_bytes)


@pytest.fixture
def analyze_photo_tool_no_photos(bonsai_item):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return bonsai_item if name == bonsai_item.name else None

    def list_bonsai_photos(bonsai_id: int) -> list:
        return []

    def load_photo_bytes(file_path: str) -> bytes | None:
        return b"fake_photo_bytes"

    return create_analyze_bonsai_photo_tool(get_bonsai_by_name, list_bonsai_photos, load_photo_bytes)


@pytest.fixture
def analyze_photo_tool_missing_file(bonsai_item, photo_item):
    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return bonsai_item if name == bonsai_item.name else None

    def list_bonsai_photos(bonsai_id: int) -> list:
        return [photo_item] if bonsai_id == bonsai_item.id else []

    def load_photo_bytes(file_path: str) -> bytes | None:
        return None

    return create_analyze_bonsai_photo_tool(get_bonsai_by_name, list_bonsai_photos, load_photo_bytes)


class FakeToolContext:
    def __init__(self):
        self.state = {}
