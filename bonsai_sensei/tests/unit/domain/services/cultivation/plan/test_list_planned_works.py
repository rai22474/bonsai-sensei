import calendar
from datetime import date

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.works.list_planned_works import create_list_planned_works_tool


def should_return_error_when_bonsai_not_found():
    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: None,
        list_planned_works_in_date_range_func=lambda **_: [],
    )

    result = tool("Unknown")

    assert_that(result["status"], equal_to("error"), "Expected error status when bonsai does not exist")


def should_return_bonsai_not_found_message_when_bonsai_missing():
    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: None,
        list_planned_works_in_date_range_func=lambda **_: [],
    )

    result = tool("Unknown")

    assert_that(result["message"], equal_to("bonsai_not_found"), "Expected bonsai_not_found error message")


def should_return_success_status_when_bonsai_exists():
    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=lambda **_: [],
    )

    result = tool("Hanako")

    assert_that(result["status"], equal_to("success"), "Expected success status when bonsai exists")


def should_return_empty_list_when_no_works_in_current_month():
    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=lambda **_: [],
    )

    result = tool("Hanako")

    assert_that(result["planned_works"], equal_to([]), "Expected empty list when no works scheduled this month")


def should_return_works_scheduled_within_current_month():
    today = date(2026, 6, 8)
    work = _make_work(bonsai_id=1, scheduled_date=date(2026, 6, 15))

    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=lambda **_: [work],
        get_today_func=lambda: today,
    )

    result = tool("Hanako")

    assert_that(len(result["planned_works"]), equal_to(1), "Expected one work returned for current month")


def should_query_with_start_of_current_month():
    today = date(2026, 6, 8)
    captured = {}

    def capture_range(**kwargs):
        captured.update(kwargs)
        return []

    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=capture_range,
        get_today_func=lambda: today,
    )
    tool("Hanako")

    assert_that(captured["start_date"], equal_to(date(2026, 6, 1)), "Expected start_date to be first day of month")


def should_query_with_end_of_current_month():
    today = date(2026, 6, 8)
    captured = {}

    def capture_range(**kwargs):
        captured.update(kwargs)
        return []

    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=capture_range,
        get_today_func=lambda: today,
    )
    tool("Hanako")

    assert_that(captured["end_date"], equal_to(date(2026, 6, 30)), "Expected end_date to be last day of month")


def should_pass_bonsai_id_to_date_range_query():
    today = date(2026, 6, 8)
    captured = {}

    def capture_range(**kwargs):
        captured.update(kwargs)
        return []

    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(42, name),
        list_planned_works_in_date_range_func=capture_range,
        get_today_func=lambda: today,
    )
    tool("Hanako")

    assert_that(captured["bonsai_id"], equal_to(42), "Expected bonsai_id passed to date range query")


def should_include_work_type_in_result():
    today = date(2026, 6, 8)
    work = _make_work(bonsai_id=1, scheduled_date=date(2026, 6, 15))

    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=lambda **_: [work],
        get_today_func=lambda: today,
    )

    result = tool("Hanako")

    assert_that(result["planned_works"][0]["work_type"], equal_to("fertilizer_application"), "Expected work_type in result")


def should_include_scheduled_date_as_iso_string():
    today = date(2026, 6, 8)
    work = _make_work(bonsai_id=1, scheduled_date=date(2026, 6, 15))

    tool = create_list_planned_works_tool(
        get_bonsai_by_name_func=lambda name: _make_bonsai(1, name),
        list_planned_works_in_date_range_func=lambda **_: [work],
        get_today_func=lambda: today,
    )

    result = tool("Hanako")

    assert_that(result["planned_works"][0]["scheduled_date"], equal_to("2026-06-15"), "Expected ISO date string")


def _make_bonsai(bonsai_id: int, name: str) -> Bonsai:
    bonsai = Bonsai(name=name, species_id=1)
    bonsai.id = bonsai_id
    return bonsai


def _make_work(bonsai_id: int, scheduled_date: date) -> PlannedWork:
    work = PlannedWork(
        bonsai_id=bonsai_id,
        work_type="fertilizer_application",
        payload={"fertilizer_name": "Bio", "amount": "5 ml"},
        scheduled_date=scheduled_date,
    )
    work.id = 1
    return work
