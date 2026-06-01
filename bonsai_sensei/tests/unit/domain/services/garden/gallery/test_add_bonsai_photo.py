from datetime import date

import pytest
from hamcrest import assert_that, equal_to, has_length

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.bonsai_photo import BonsaiPhoto
from bonsai_sensei.domain.services.human_input import ConfirmationResult, SelectionNoneResult
from bonsai_sensei.domain.services.garden.gallery.add_bonsai_photo import create_add_bonsai_photo_tool


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


@pytest.mark.asyncio
async def should_return_error_when_no_pending_photo(add_photo_tool_no_pending, tool_context):
    result = await add_photo_tool_no_pending(bonsai_name="Olmo", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "no_pending_photo"}),
        "Missing pending photo should return no_pending_photo error")


@pytest.mark.asyncio
async def should_return_error_when_no_bonsai_available(tool_context):
    tool = create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: None,
        list_bonsai_func=lambda: [],
        create_bonsai_photo_func=lambda bonsai_photo: bonsai_photo,
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: b"photo_data",
        save_photo_file=lambda name, data: "some/path.jpg",
        clear_pending_photo=lambda user_id: None,
    )

    result = await tool(bonsai_name="", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "no_bonsai_available"}),
        "Empty bonsai list should return no_bonsai_available error")


@pytest.mark.asyncio
async def should_return_error_when_bonsai_not_found(add_photo_tool, tool_context):
    result = await add_photo_tool(bonsai_name="Unknown", tool_context=tool_context)

    assert_that(result, equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return bonsai_not_found error")


@pytest.mark.asyncio
async def should_return_cancelled_when_selection_is_cancelled(tool_context, existing_bonsai):
    async def ask_selection_cancel(question, options, tool_context=None):
        return SelectionNoneResult(reason="changed mind")

    tool = create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_func=lambda: [existing_bonsai],
        create_bonsai_photo_func=lambda bonsai_photo: bonsai_photo,
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_cancel,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: b"photo_data",
        save_photo_file=lambda name, data: "some/path.jpg",
        clear_pending_photo=lambda user_id: None,
    )

    result = await tool(bonsai_name="", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Cancelled selection should return cancelled status")


@pytest.mark.asyncio
async def should_save_photo_and_create_record_when_confirmed(add_photo_tool, tool_context, captured_photos):
    await add_photo_tool(bonsai_name="Olmo", tool_context=tool_context)

    assert_that(captured_photos, has_length(1), "One photo record should be created when confirmed")


@pytest.mark.asyncio
async def should_return_success_when_confirmed(add_photo_tool, tool_context):
    result = await add_photo_tool(bonsai_name="Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("success"),
        "Tool should return success status when user confirms")


@pytest.mark.asyncio
async def should_return_cancelled_when_user_declines_confirmation(tool_context, existing_bonsai, captured_photos):
    tool = create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_func=lambda: [existing_bonsai],
        create_bonsai_photo_func=lambda bonsai_photo: captured_photos.append(bonsai_photo),
        ask_confirmation=ask_confirmation_cancel,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: b"photo_data",
        save_photo_file=lambda name, data: "some/path.jpg",
        clear_pending_photo=lambda user_id: None,
    )

    result = await tool(bonsai_name="Olmo", tool_context=tool_context)

    assert_that(result["status"], equal_to("cancelled"),
        "Tool should return cancelled when user declines confirmation")


@pytest.mark.asyncio
async def should_clear_pending_photo_after_confirmation(tool_context, existing_bonsai):
    cleared_for = []

    tool = create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_func=lambda: [existing_bonsai],
        create_bonsai_photo_func=lambda bonsai_photo: None,
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: b"photo_data",
        save_photo_file=lambda name, data: "some/path.jpg",
        clear_pending_photo=lambda user_id: cleared_for.append(user_id),
    )

    await tool(bonsai_name="Olmo", tool_context=tool_context)

    assert_that(cleared_for, has_length(1), "Pending photo should be cleared after confirmation")


@pytest.mark.asyncio
async def should_clear_pending_photo_after_cancellation(tool_context, existing_bonsai):
    cleared_for = []

    tool = create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_func=lambda: [existing_bonsai],
        create_bonsai_photo_func=lambda bonsai_photo: None,
        ask_confirmation=ask_confirmation_cancel,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: b"photo_data",
        save_photo_file=lambda name, data: "some/path.jpg",
        clear_pending_photo=lambda user_id: cleared_for.append(user_id),
    )

    await tool(bonsai_name="Olmo", tool_context=tool_context)

    assert_that(cleared_for, has_length(1), "Pending photo should be cleared after cancellation")


async def ask_confirmation_confirm(question, tool_context=None):
    return ConfirmationResult(accepted=True)


async def ask_confirmation_cancel(question, tool_context=None):
    return ConfirmationResult(accepted=False, reason="user declined")


async def ask_selection_confirm(question, options, tool_context=None):
    return options[0] if options else SelectionNoneResult(reason="no options")


@pytest.fixture
def existing_bonsai():
    return Bonsai(id=1, name="Olmo", species_id=1)


@pytest.fixture
def captured_photos():
    return []


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def add_photo_tool(existing_bonsai, captured_photos):
    return create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_func=lambda: [existing_bonsai],
        create_bonsai_photo_func=lambda bonsai_photo: captured_photos.append(bonsai_photo),
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: b"photo_data",
        save_photo_file=lambda name, data: "bonsai/olmo/photo.jpg",
        clear_pending_photo=lambda user_id: None,
    )


@pytest.fixture
def add_photo_tool_no_pending(existing_bonsai):
    return create_add_bonsai_photo_tool(
        get_bonsai_by_name_func=lambda name: existing_bonsai if name == existing_bonsai.name else None,
        list_bonsai_func=lambda: [existing_bonsai],
        create_bonsai_photo_func=lambda bonsai_photo: None,
        ask_confirmation=ask_confirmation_confirm,
        ask_selection=ask_selection_confirm,
        build_selection_question=lambda: "Select bonsai",
        build_confirmation_message=lambda name: f"Confirm photo for '{name}'",
        get_pending_photo_bytes=lambda user_id: None,
        save_photo_file=lambda name, data: "some/path.jpg",
        clear_pending_photo=lambda user_id: None,
    )
