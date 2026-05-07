from datetime import date, datetime, timezone
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.cultivation.plan.fertilization.wiki import update_wiki_on_abandon
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_abandon_fertilization_plan_tool(
    get_bonsai_by_name_func: Callable,
    get_active_fertilization_plan_func: Callable,
    update_fertilization_plan_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def abandon_fertilization_plan(
        bonsai_name: str,
        reason: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Abandon the active fertilization plan for a bonsai after explicit user confirmation. Marks the plan as abandoned, records the reason, deletes all future scheduled work from this plan, and updates the wiki page.

        Args:
            bonsai_name: Name of the bonsai whose active fertilization plan should be abandoned.
            reason: Explanation for why the plan is being abandoned.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "plan_id": int}.
            Output JSON (cancelled): {"status": "cancelled", "reason": str}.
            Output JSON (error): {"status": "error", "message": "bonsai_not_found" | "no_active_plan"}.
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        plan = get_active_fertilization_plan_func(bonsai_id=bonsai.id)
        if not plan:
            return {"status": "error", "message": "no_active_plan"}

        confirmation_message = build_confirmation_message(
            bonsai_name,
            plan.period_start.isoformat(),
            plan.period_end.isoformat(),
            reason,
        )
        confirmed = await ask_confirmation(confirmation_message, tool_context=tool_context)
        if not confirmed:
            return {"status": "cancelled", "reason": confirmed.reason}

        today = date.today()
        delete_future_planned_works_func(plan_id=plan.id, cutoff_date=today)

        plan.status = "abandoned"
        plan.abandonment_reason = reason
        plan.abandoned_at = datetime.now(timezone.utc)
        update_fertilization_plan_func(plan)

        update_wiki_on_abandon(plan.wiki_path, reason, read_wiki_page_func, write_wiki_page_func)

        return {"status": "success", "plan_id": plan.id}

    return abandon_fertilization_plan
