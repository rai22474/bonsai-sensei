from datetime import date

import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.mimamori.context import build_work_summaries


def should_return_empty_list_when_no_works():
    result = build_work_summaries(planned_works=[], bonsai_map={})
    assert_that(result, equal_to([]))


def should_map_bonsai_id_to_name():
    work = _make_work(bonsai_id=5, work_type="fertilizer_application", scheduled_date=date(2026, 6, 15))
    result = build_work_summaries(planned_works=[work], bonsai_map={5: "Hanako"})
    assert_that(result[0]["bonsai_name"], equal_to("Hanako"))


def should_use_fallback_name_when_bonsai_not_in_map():
    work = _make_work(bonsai_id=99, work_type="watering", scheduled_date=date(2026, 6, 15))
    result = build_work_summaries(planned_works=[work], bonsai_map={})
    assert_that(result[0]["bonsai_name"], equal_to("Bonsái 99"))


def should_include_work_type():
    work = _make_work(bonsai_id=1, work_type="phytosanitary_application", scheduled_date=date(2026, 6, 15))
    result = build_work_summaries(planned_works=[work], bonsai_map={1: "Kuro"})
    assert_that(result[0]["work_type"], equal_to("phytosanitary_application"))


def should_format_scheduled_date_as_iso_string():
    work = _make_work(bonsai_id=1, work_type="watering", scheduled_date=date(2026, 7, 4))
    result = build_work_summaries(planned_works=[work], bonsai_map={1: "Kuro"})
    assert_that(result[0]["scheduled_date"], equal_to("2026-07-04"))


def should_return_one_entry_per_work():
    works = [
        _make_work(bonsai_id=1, work_type="watering", scheduled_date=date(2026, 6, 1)),
        _make_work(bonsai_id=2, work_type="fertilizer_application", scheduled_date=date(2026, 6, 15)),
    ]
    result = build_work_summaries(planned_works=works, bonsai_map={1: "Hanako", 2: "Kuro"})
    assert_that(len(result), equal_to(2))


def _make_work(bonsai_id: int, work_type: str, scheduled_date: date) -> PlannedWork:
    work = PlannedWork(bonsai_id=bonsai_id, work_type=work_type, payload={}, scheduled_date=scheduled_date)
    work.id = 1
    return work
