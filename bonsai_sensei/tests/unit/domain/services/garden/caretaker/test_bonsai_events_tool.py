import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.services.garden.caretaker.bonsai_events_tool import create_list_bonsai_events_tool


def should_return_error_when_bonsai_name_is_missing_in_list_events(list_bonsai_events_tool):
    result = list_bonsai_events_tool("")

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_name_required"}),
        "Empty bonsai_name should return bonsai_name_required error",
    )


def should_return_error_when_bonsai_not_found_in_list_events(list_bonsai_events_tool):
    result = list_bonsai_events_tool("Unknown Bonsai")

    assert_that(
        result,
        equal_to({"status": "error", "message": "bonsai_not_found"}),
        "Unknown bonsai name should return bonsai_not_found error",
    )


def should_return_empty_events_list_when_bonsai_has_no_events(list_bonsai_events_tool_no_events):
    result = list_bonsai_events_tool_no_events("Olmo 1")

    assert_that(
        result,
        equal_to({"status": "success", "events": []}),
        "Bonsai with no events should return empty list",
    )


def should_return_events_for_bonsai(list_bonsai_events_tool):
    result = list_bonsai_events_tool("Olmo 1")

    assert_that(
        result["status"],
        equal_to("success"),
        "Valid bonsai name should return success status",
    )
    assert_that(
        result["events"],
        equal_to(
            [
                {
                    "event_type": "fertilizer_application",
                    "payload": {"fertilizer_name": "BioGrow", "amount": "5 ml"},
                }
            ]
        ),
        "Events list should match the events returned by list_bonsai_events_func",
    )


@pytest.fixture
def list_bonsai_events_tool():
    bonsai_item = Bonsai(id=1, name="Olmo 1", species_id=1)
    stored_events = [
        {
            "event_type": "fertilizer_application",
            "payload": {"fertilizer_name": "BioGrow", "amount": "5 ml"},
        }
    ]

    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return bonsai_item if name == bonsai_item.name else None

    def list_bonsai_events_func(bonsai_id: int) -> list[dict]:
        return stored_events if bonsai_id == bonsai_item.id else []

    return create_list_bonsai_events_tool(get_bonsai_by_name, list_bonsai_events_func)


@pytest.fixture
def list_bonsai_events_tool_no_events():
    bonsai_item = Bonsai(id=1, name="Olmo 1", species_id=1)

    def get_bonsai_by_name(name: str) -> Bonsai | None:
        return bonsai_item if name == bonsai_item.name else None

    def list_bonsai_events_func(bonsai_id: int) -> list[dict]:
        return []

    return create_list_bonsai_events_tool(get_bonsai_by_name, list_bonsai_events_func)
