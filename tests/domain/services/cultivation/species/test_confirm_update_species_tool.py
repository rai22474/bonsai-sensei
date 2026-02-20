import pytest
from hamcrest import assert_that, equal_to, not_none

from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.cultivation.species.confirm_update_species_tool import (
    create_confirm_update_species_tool,
)
from bonsai_sensei.domain.species import Species


class MockToolContext:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.state = {}


def should_return_error_when_tool_context_is_none(update_tool, new_update):
    result = update_tool(**new_update, tool_context=None)

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "Missing tool_context should return a user_id required error",
    )


def should_return_error_when_tool_context_has_no_user_id(update_tool, new_update):
    result = update_tool(**new_update, tool_context=MockToolContext(user_id=None))

    assert_that(
        result,
        equal_to({"status": "error", "message": "user_id_required_for_confirmation"}),
        "tool_context without user_id should return a user_id required error",
    )


def should_return_error_when_species_name_is_missing(update_tool, tool_context):
    result = update_tool(
        species={"scientific_name": "Ulmus minor"},
        summary="Summary",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_name_required"}),
        "species dict without name or common_name should return a species_name_required error",
    )


def should_return_error_when_no_fields_to_update(update_tool, tool_context):
    result = update_tool(
        species={"name": "Elm"},
        summary="Summary",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_update_required"}),
        "species dict with only the identifier and no update fields should return a species_update_required error",
    )


def should_return_error_when_species_not_found(update_tool, tool_context):
    result = update_tool(
        species={"name": "Unknown", "scientific_name": "Unknownus"},
        summary="Summary",
        tool_context=tool_context,
    )

    assert_that(
        result,
        equal_to({"status": "error", "message": "species_not_found"}),
        "A name that does not match any species should return a species_not_found error",
    )


def should_return_confirmation_summary_when_update_is_valid(
    update_tool, tool_context, new_update
):
    result = update_tool(**new_update, tool_context=tool_context)

    assert_that(
        result,
        equal_to({"confirmation": new_update["summary"]}),
        "Valid update input should return a confirmation dict with the summary",
    )


def should_store_pending_confirmation_in_store(
    update_tool, tool_context, confirmation_store, new_update
):
    update_tool(**new_update, tool_context=tool_context)

    assert_that(
        confirmation_store.get_pending("user-123"),
        not_none(),
        "Pending confirmation should be stored in the store",
    )


def should_store_confirmation_with_correct_user_id(pending_confirmation):
    assert_that(
        pending_confirmation.user_id,
        equal_to("user-123"),
        "Stored confirmation should carry the correct user_id",
    )


def should_store_confirmation_with_correct_summary(pending_confirmation, new_update):
    assert_that(
        pending_confirmation.summary,
        equal_to(new_update["summary"]),
        "Stored confirmation summary should match the argument",
    )


def should_execute_update_with_correct_species_id(executed_update):
    assert_that(
        executed_update["species_id"],
        equal_to(1),
        "Executor should pass the existing species id to update_species_func",
    )


def should_execute_update_with_scientific_name_in_species_data(executed_update):
    assert_that(
        executed_update["species_data"]["scientific_name"],
        equal_to("Ulmus minor"),
        "Executor should include scientific_name in species_data",
    )


def should_execute_update_with_common_name_in_species_data(update_tool, tool_context, confirmation_store, captured_update):
    update_tool(
        species={"name": "Elm", "common_name": "English Elm"},
        summary="Rename species",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()

    assert_that(
        captured_update["species_data"]["name"],
        equal_to("English Elm"),
        "Executor should include the new common_name mapped to 'name' in species_data",
    )


def should_store_both_confirmations_when_updated_twice(
    update_tool, tool_context, confirmation_store
):
    update_tool(
        species={"name": "Elm", "scientific_name": "Ulmus minor"},
        summary="First update",
        tool_context=tool_context,
    )
    update_tool(
        species={"name": "Elm", "scientific_name": "Ulmus glabra"},
        summary="Second update",
        tool_context=tool_context,
    )

    assert_that(
        len(confirmation_store.get_all_pending("user-123")),
        equal_to(2),
        "Both confirmations should be stored independently for the same user",
    )


@pytest.fixture
def confirmation_store():
    return ConfirmationStore()


@pytest.fixture
def captured_update():
    return {}


@pytest.fixture
def update_species_func(captured_update):
    def update_species(species_id: int, species_data: dict) -> None:
        captured_update["species_id"] = species_id
        captured_update["species_data"] = species_data

    return update_species


@pytest.fixture
def existing_species():
    return Species(id=1, name="Elm", scientific_name="Ulmus", care_guide={})


@pytest.fixture
def get_species_by_name_func(existing_species):
    def get_species_by_name(name: str) -> Species | None:
        return existing_species if name == existing_species.name else None

    return get_species_by_name


@pytest.fixture
def update_tool(update_species_func, get_species_by_name_func, confirmation_store):
    return create_confirm_update_species_tool(
        update_species_func, get_species_by_name_func, confirmation_store
    )


@pytest.fixture
def tool_context():
    return MockToolContext(user_id="user-123")


@pytest.fixture
def new_update():
    return {
        "species": {"name": "Elm", "scientific_name": "Ulmus minor"},
        "summary": "Update Elm scientific name",
    }


@pytest.fixture
def pending_confirmation(update_tool, tool_context, confirmation_store, new_update):
    update_tool(**new_update, tool_context=tool_context)
    return confirmation_store.get_pending("user-123")


@pytest.fixture
def executed_update(update_tool, tool_context, confirmation_store, captured_update):
    update_tool(
        species={"name": "Elm", "scientific_name": "Ulmus minor"},
        summary="Summary",
        tool_context=tool_context,
    )
    pending = confirmation_store.get_pending("user-123")
    pending.execute()
    return captured_update
