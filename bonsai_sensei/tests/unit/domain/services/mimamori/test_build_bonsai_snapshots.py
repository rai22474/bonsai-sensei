from datetime import datetime, timezone

from hamcrest import assert_that, equal_to, none, not_none

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.development_plan import DevelopmentPlan
from bonsai_sensei.domain.fertilization_plan import FertilizationPlan
from bonsai_sensei.domain.services.mimamori.context import build_bonsai_snapshots


def should_include_bonsai_name_in_snapshot():
    bonsai = _make_bonsai(1, "Hanako", species_id=10)
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={10: "Ficus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: None,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["name"], equal_to("Hanako"))


def should_resolve_species_name_from_map():
    bonsai = _make_bonsai(1, "Hanako", species_id=10)
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={10: "Ficus retusa"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: None,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["species_name"], equal_to("Ficus retusa"))


def should_use_unknown_species_when_not_in_map():
    bonsai = _make_bonsai(1, "Hanako", species_id=99)
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: None,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["species_name"], equal_to("Especie desconocida"))


def should_include_development_phase_when_plan_exists():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    dev_plan = _make_dev_plan(current_phase="engorde", design_goal="trunk thickening", created_at=_dt(2025, 1, 1))
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: dev_plan,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["development_phase"], equal_to("engorde"))


def should_have_none_development_phase_when_no_plan():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: None,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["development_phase"], none())


def should_detect_fertilization_outdated_when_design_plan_newer():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    fert_plan = _make_fert_plan(goal="engorde", created_at=_dt(2025, 1, 1))
    dev_plan = _make_dev_plan(current_phase="refinamiento", design_goal="new goal", created_at=_dt(2025, 6, 1))
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: dev_plan,
        get_active_fertilization_plan_func=lambda **_: fert_plan,
    )
    assert_that(result[0]["fertilization_outdated"], equal_to(True))


def should_not_flag_outdated_when_fertilization_plan_newer():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    dev_plan = _make_dev_plan(current_phase="engorde", design_goal="goal", created_at=_dt(2025, 1, 1))
    fert_plan = _make_fert_plan(goal="engorde", created_at=_dt(2025, 6, 1))
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: dev_plan,
        get_active_fertilization_plan_func=lambda **_: fert_plan,
    )
    assert_that(result[0]["fertilization_outdated"], equal_to(False))


def should_not_flag_outdated_when_no_fertilization_plan():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    dev_plan = _make_dev_plan(current_phase="engorde", design_goal="goal", created_at=_dt(2025, 6, 1))
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: dev_plan,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["fertilization_outdated"], equal_to(False))


def should_include_outdated_goals_when_fertilization_outdated():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    fert_plan = _make_fert_plan(goal="old goal", created_at=_dt(2025, 1, 1))
    dev_plan = _make_dev_plan(current_phase="refinamiento", design_goal="new goal", created_at=_dt(2025, 6, 1))
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: dev_plan,
        get_active_fertilization_plan_func=lambda **_: fert_plan,
    )
    assert_that(result[0]["fertilization_plan_goal"], equal_to("old goal"))
    assert_that(result[0]["current_design_goal"], equal_to("new goal"))


def should_include_last_event_when_events_exist():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    events = [
        {"event_type": "fertilizer_application", "occurred_at": "2026-03-01T10:00:00"},
        {"event_type": "watering", "occurred_at": "2026-05-15T08:00:00"},
    ]
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: events,
        get_active_development_plan_func=lambda **_: None,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["last_event_type"], equal_to("watering"))


def should_have_none_last_event_when_no_events():
    bonsai = _make_bonsai(1, "Hanako", species_id=1)
    result = build_bonsai_snapshots(
        bonsais=[bonsai],
        species_map={1: "Pinus"},
        list_bonsai_events_func=lambda **_: [],
        get_active_development_plan_func=lambda **_: None,
        get_active_fertilization_plan_func=lambda **_: None,
    )
    assert_that(result[0]["last_event_type"], none())


def _make_bonsai(bonsai_id: int, name: str, species_id: int) -> Bonsai:
    bonsai = Bonsai(name=name, species_id=species_id)
    bonsai.id = bonsai_id
    return bonsai


def _make_dev_plan(current_phase: str, design_goal: str, created_at: datetime) -> DevelopmentPlan:
    plan = DevelopmentPlan(
        bonsai_id=1,
        development_path="planton",
        current_phase=current_phase,
        target_style="moyogi",
        design_goal=design_goal,
        period_start="2025-01-01",
        period_end="2025-12-31",
        status="active",
    )
    plan.created_at = created_at
    return plan


def _make_fert_plan(goal: str, created_at: datetime) -> FertilizationPlan:
    plan = FertilizationPlan(
        bonsai_id=1,
        period_start="2025-01-01",
        period_end="2025-12-31",
        status="active",
        goal=goal,
    )
    plan.created_at = created_at
    return plan


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)
