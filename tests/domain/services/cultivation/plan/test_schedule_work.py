import pytest
from hamcrest import assert_that, equal_to

from bonsai_sensei.domain.services.cultivation.plan.schedule_work import schedule_work
from bonsai_sensei.domain.services.human_input import SelectionNoneResult


@pytest.mark.asyncio
async def should_call_plan_func_when_period_provided(schedule_deps):
    result = await schedule_work(**schedule_deps, scheduled_date="", period_start="2026-09-01", period_end="2026-11-30", product_extra={}, tool_context=None)

    assert_that(result, equal_to({"status": "success", "type": "plan", "start": "2026-09-01", "end": "2026-11-30"}))


@pytest.mark.asyncio
async def should_call_one_time_func_when_date_provided(schedule_deps):
    result = await schedule_work(**schedule_deps, scheduled_date="2026-07-15", period_start="", period_end="", product_extra={"fertilizer_name": "BioGrow"}, tool_context=None)

    assert_that(result, equal_to({"status": "success", "type": "puntual", "date": "2026-07-15", "fertilizer_name": "BioGrow"}))


@pytest.mark.asyncio
async def should_ask_selection_when_no_date(schedule_deps):
    schedule_deps["ask_selection"] = _make_ask_selection_returning("Fertilización puntual")

    result = await schedule_work(**schedule_deps, scheduled_date="", period_start="", period_end="", product_extra={}, tool_context=None)

    assert_that(result, equal_to({"status": "success", "type": "puntual", "date": ""}))


@pytest.mark.asyncio
async def should_ask_period_when_plan_chosen(schedule_deps):
    schedule_deps["ask_selection"] = _make_ask_selection_returning("Plan de fertilización")
    schedule_deps["ask_human"] = _make_ask_human_returning("del 2026-09-01 al 2026-11-30")

    result = await schedule_work(**schedule_deps, scheduled_date="", period_start="", period_end="", product_extra={}, tool_context=None)

    assert_that(result, equal_to({"status": "success", "type": "plan", "start": "2026-09-01", "end": "2026-11-30"}))


@pytest.mark.asyncio
async def should_return_cancelled_when_user_cancels_selection(schedule_deps):
    schedule_deps["ask_selection"] = _make_ask_selection_returning(SelectionNoneResult(reason="user_cancelled"))

    result = await schedule_work(**schedule_deps, scheduled_date="", period_start="", period_end="", product_extra={}, tool_context=None)

    assert_that(result, equal_to({"status": "cancelled", "message": "user_cancelled"}))


@pytest.mark.asyncio
async def should_return_error_when_period_text_has_no_valid_dates(schedule_deps):
    schedule_deps["ask_selection"] = _make_ask_selection_returning("Plan de fertilización")
    schedule_deps["ask_human"] = _make_ask_human_returning("no sé, en algún momento del verano")

    result = await schedule_work(**schedule_deps, scheduled_date="", period_start="", period_end="", product_extra={}, tool_context=None)

    assert_that(result, equal_to({"status": "error", "message": "invalid_date_format"}))


@pytest.mark.asyncio
async def should_pass_product_extra_to_puntual_func(schedule_deps):
    result = await schedule_work(**schedule_deps, scheduled_date="2026-07-15", period_start="", period_end="", product_extra={"phytosanitary_name": "Neem", "amount": "2ml"}, tool_context=None)

    assert_that(result["phytosanitary_name"], equal_to("Neem"), "product_extra keys should be forwarded to run_one_time_func")


# --- fixtures ---

@pytest.fixture
def schedule_deps():
    options = ["Fertilización puntual", "Plan de fertilización"]
    return {
        "run_one_time_func": _make_puntual_func(),
        "run_plan_func": _make_plan_func(),
        "ask_selection": _make_ask_selection_returning(options[0]),
        "ask_human": _make_ask_human_returning("2026-09-01 al 2026-11-30"),
        "build_type_question": lambda: "¿Puntual o plan?",
        "build_type_options": lambda: options,
        "build_period_question": lambda bonsai_name: f"¿Período para {bonsai_name}?",
        "bonsai_name": "Kaze",
    }


def _make_puntual_func():
    async def run_one_time_func(bonsai_name, scheduled_date, tool_context, **kwargs):
        return {"status": "success", "type": "puntual", "date": scheduled_date, **kwargs}
    return run_one_time_func


def _make_plan_func():
    async def run_plan_func(bonsai_name, start_date, end_date, tool_context):
        return {"status": "success", "type": "plan", "start": start_date, "end": end_date}
    return run_plan_func


def _make_ask_selection_returning(value):
    async def ask_selection(question, options, tool_context):
        return value
    return ask_selection


def _make_ask_human_returning(value):
    async def ask_human(question, tool_context):
        return value
    return ask_human
