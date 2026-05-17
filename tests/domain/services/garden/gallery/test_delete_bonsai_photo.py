from datetime import date

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.human_input import ConfirmationResult, SelectionNoneResult
from bonsai_sensei.domain.services.garden.gallery.delete_bonsai_photo import create_delete_bonsai_photo_tool


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(delete_photo_tool, tool_context):
    result = await delete_photo_tool("Unknown", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_error_when_no_photos_available(delete_photo_tool_no_photos, tool_context):
    result = await delete_photo_tool_no_photos("Olmo", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "no_photos_available"}),
        "Bonsai with no photos should return no_photos_available error")


@pytest.mark.asyncio
async def should_return_cancelled_when_selection_is_cancelled(tool_context, existing_bonsai, existing_photo):
    async def ask_selection_cancel(question, options, tool_context=None, **kwargs):
        return SelectionNoneResult(reason="changed mind")

    tool = create_delete_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [existing_photo] if bonsai_id == existing_bonsai.id else [],
        delete_bonsai_photo_func=lambda photo_id: None,
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_cancel,
        build_selection_question=lambda name: f"Select photo for '{name}'",
        build_confirmation_message=lambda name, taken_on: f"Delete photo from {taken_on}?",
        build_photo_option_label=lambda taken_on: str(taken_on),
    )

    result = await tool("Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Cancelled selection should return cancelled status")


@pytest.mark.asyncio
async def should_delete_photo_record_when_confirmed(delete_photo_tool, tool_context, deleted_photo_ids):
    await delete_photo_tool("Olmo", tool_context=tool_context)

    assert_that(deleted_photo_ids, equal_to([1]), "Photo with id=1 should be deleted when confirmed")


@pytest.mark.asyncio
async def should_return_success_when_confirmed(delete_photo_tool, tool_context):
    result = await delete_photo_tool("Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines_confirmation(tool_context, existing_bonsai, existing_photo):
    tool = create_delete_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [existing_photo] if bonsai_id == existing_bonsai.id else [],
        delete_bonsai_photo_func=lambda photo_id: None,
        ask_confirmation=ask_confirmation_cancel,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda name: f"Select photo for '{name}'",
        build_confirmation_message=lambda name, taken_on: f"Delete photo from {taken_on}?",
        build_photo_option_label=lambda taken_on: str(taken_on),
    )

    result = await tool("Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled when user declines confirmation")


async def ask_confirmation_confirm(question, tool_context=None):
    return ConfirmationResult(accepted=True)


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False, reason="user declined")


async def ask_selection_confirm(question, options, tool_context=None, **kwargs):
    return options[0] if options else SelectionNoneResult(reason="no options")


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Olmo", species_id=1)


@pytest.fixture
def existing_photo():
    return BonsaiPhoto(id=1, bonsai_id=1, file_path="bonsai/olmo/photo1.jpg", taken_on=date(2025, 3, 15))


@pytest.fixture
def deleted_photo_ids():
    return []


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def delete_photo_tool(existing_bonsai, existing_photo, deleted_photo_ids):
    return create_delete_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [existing_photo] if bonsai_id == existing_bonsai.id else [],
        delete_bonsai_photo_func=lambda photo_id: deleted_photo_ids.append(photo_id),
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda name: f"Select photo for '{name}'",
        build_confirmation_message=lambda name, taken_on: f"Delete photo from {taken_on}?",
        build_photo_option_label=lambda taken_on: str(taken_on),
    )


@pytest.fixture
def delete_photo_tool_no_photos(existing_bonsai):
    return create_delete_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_photos_func=lambda bonsai_id: [],
        delete_bonsai_photo_func=lambda photo_id: None,
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda name: f"Select photo for '{name}'",
        build_confirmation_message=lambda name, taken_on: f"Delete photo from {taken_on}?",
        build_photo_option_label=lambda taken_on: str(taken_on),
    )
