from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_delete_planned_work_tool(
    get_planned_work_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="planning_agent")
    async def confirm_delete_planned_work(
        planned_work_id: int,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a planned work after explicit user confirmation.

        Args:
            planned_work_id: ID of the planned work to delete.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "planned_work_not_found".
        """
        work = get_planned_work_func(work_id=planned_work_id)
        if not work:
            return {"status": "error", "message": "planned_work_not_found"}

        confirmation_message = build_confirmation_message(work)
        confirmed = await ask_confirmation(confirmation_message, tool_context=tool_context)

        if confirmed:
            delete_planned_work_func(work_id=planned_work_id)
            return {"status": "success", "message": f"Planned work {planned_work_id} deleted."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_delete_planned_work
