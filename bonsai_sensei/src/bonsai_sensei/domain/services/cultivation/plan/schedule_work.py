import re
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.human_input import SelectionNoneResult


async def schedule_work(
    run_one_time_func: Callable,
    run_plan_func: Callable,
    ask_selection: Callable,
    ask_human: Callable,
    build_type_question: Callable,
    build_type_options: Callable,
    build_period_question: Callable,
    bonsai_name: str,
    scheduled_date: str,
    period_start: str,
    period_end: str,
    product_extra: dict,
    tool_context: ToolContext | None,
) -> dict:
    if period_start and period_end:
        return await run_plan_func(bonsai_name=bonsai_name, start_date=period_start, end_date=period_end, tool_context=tool_context)

    if scheduled_date:
        return await run_one_time_func(bonsai_name=bonsai_name, scheduled_date=scheduled_date, **product_extra, tool_context=tool_context)

    options = build_type_options()
    choice = await ask_selection(question=build_type_question(), options=options, tool_context=tool_context)
    if isinstance(choice, SelectionNoneResult):
        return {"status": "cancelled", "message": "user_cancelled"}

    if choice == options[0]:
        return await run_one_time_func(bonsai_name=bonsai_name, scheduled_date="", **product_extra, tool_context=tool_context)

    period_text = await ask_human(question=build_period_question(bonsai_name), tool_context=tool_context)
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", period_text)
    if len(dates) < 2:
        return {"status": "error", "message": "invalid_date_format"}

    return await run_plan_func(bonsai_name=bonsai_name, start_date=dates[0], end_date=dates[1], tool_context=tool_context)
