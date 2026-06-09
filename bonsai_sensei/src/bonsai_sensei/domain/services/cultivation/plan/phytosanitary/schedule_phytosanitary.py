from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.cultivation.plan.works.schedule_work import schedule_work
from bonsai_sensei.domain.services.human_input import resolve_bonsai_name
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_schedule_phytosanitary_tool(
    run_one_time_func: Callable,
    run_plan_func: Callable,
    ask_selection: Callable,
    ask_human: Callable,
    build_bonsai_name_question: Callable,
    build_type_question: Callable,
    build_type_options: Callable,
    build_period_question: Callable,
) -> Callable:

    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def schedule_phytosanitary(
        bonsai_name: str | None = None,
        scheduled_date: str = "",
        period_start: str = "",
        period_end: str = "",
        phytosanitary_name: str = "",
        amount: str = "",
        notes: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Schedule a phytosanitary treatment or create a multi-month phytosanitary plan for a bonsai.

        Routes automatically: if period dates are provided, creates a recurring plan; if a single date
        is provided, creates a one-off treatment; otherwise asks the user which they prefer.

        Args:
            bonsai_name: Name of the bonsai.
            scheduled_date: Date for a one-off treatment (YYYY-MM-DD). Omit if not applicable.
            period_start: Start date of the phytosanitary plan period (YYYY-MM-DD). Omit if not a plan.
            period_end: End date of the phytosanitary plan period (YYYY-MM-DD). Omit if not a plan.
            phytosanitary_name: Name of the phytosanitary product to apply.
            amount: Amount to apply (e.g. "2 ml", "5 g").
            notes: Optional notes about the planned work.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
        """
        bonsai_name = await resolve_bonsai_name(bonsai_name, ask_human, build_bonsai_name_question, tool_context)

        return await schedule_work(
            run_one_time_func=run_one_time_func,
            run_plan_func=run_plan_func,
            ask_selection=ask_selection,
            ask_human=ask_human,
            build_type_question=build_type_question,
            build_type_options=build_type_options,
            build_period_question=build_period_question,
            bonsai_name=bonsai_name,
            scheduled_date=scheduled_date,
            period_start=period_start,
            period_end=period_end,
            product_extra={"phytosanitary_name": phytosanitary_name, "amount": amount, "notes": notes},
            tool_context=tool_context,
        )

    return schedule_phytosanitary
