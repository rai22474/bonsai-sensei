from datetime import date, timedelta

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.planned_work_tools import (
    create_list_weekend_planned_works_tool,
)


def _next_saturday() -> date:
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


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


def should_return_success_status_with_saturday_and_sunday_dates():
    tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=lambda **_: [],
        list_bonsai_func=lambda: [],
    )
    saturday = _next_saturday()

    result = tool()

    assert_that(result["saturday"], equal_to(saturday.isoformat()),
        "Expected 'saturday' to be next Saturday's ISO date")
    assert_that(result["sunday"], equal_to((saturday + timedelta(days=1)).isoformat()),
        "Expected 'sunday' to be next Sunday's ISO date")


def should_return_empty_list_when_no_works_for_weekend():
    tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=lambda **_: [],
        list_bonsai_func=lambda: [],
    )

    result = tool()

    assert_that(result["planned_works"], equal_to([]),
        "Expected empty planned_works when no works are scheduled for the weekend")


def should_return_works_scheduled_for_upcoming_saturday():
    saturday = _next_saturday()
    bonsai = _make_bonsai(bonsai_id=1, name="Hanako")
    work = _make_work(bonsai_id=1, scheduled_date=saturday)

    tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=lambda **_: [work],
        list_bonsai_func=lambda: [bonsai],
    )

    result = tool()

    assert_that(len(result["planned_works"]), equal_to(1),
        "Expected one planned work for the upcoming Saturday")


def should_include_bonsai_name_in_each_work_entry():
    saturday = _next_saturday()
    bonsai = _make_bonsai(bonsai_id=7, name="Hanako")
    work = _make_work(bonsai_id=7, scheduled_date=saturday)

    tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=lambda **_: [work],
        list_bonsai_func=lambda: [bonsai],
    )

    result = tool()

    assert_that(result["planned_works"][0]["bonsai_name"], equal_to("Hanako"),
        "Expected bonsai_name to be resolved from bonsai_id in each work entry")


def should_include_work_type_and_scheduled_date_in_each_entry():
    saturday = _next_saturday()
    bonsai = _make_bonsai(bonsai_id=1, name="Kaze")
    work = _make_work(bonsai_id=1, scheduled_date=saturday)

    tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=lambda **_: [work],
        list_bonsai_func=lambda: [bonsai],
    )

    result = tool()

    entry = result["planned_works"][0]
    assert_that(entry["work_type"], equal_to("fertilizer_application"),
        "Expected work_type to be present in each work entry")
    assert_that(entry["scheduled_date"], equal_to(saturday.isoformat()),
        "Expected scheduled_date as ISO string in each work entry")


def should_query_date_range_spanning_saturday_and_sunday():
    saturday = _next_saturday()
    captured_dates = {}

    def capture_range(**kwargs):
        captured_dates.update(kwargs)
        return []

    tool = create_list_weekend_planned_works_tool(
        list_planned_works_in_date_range_func=capture_range,
        list_bonsai_func=lambda: [],
    )
    tool()

    assert_that(captured_dates["start_date"], equal_to(saturday),
        "Expected start_date to be the upcoming Saturday")
    assert_that(captured_dates["end_date"], equal_to(saturday + timedelta(days=1)),
        "Expected end_date to be the upcoming Sunday")
