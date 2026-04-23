from typing import Callable

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_execute_planned_work_tool(
    get_planned_work_func: Callable,
    record_bonsai_event_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def confirm_execute_planned_work(
        work_id: int,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Execute a planned work item after explicit user confirmation, recording the event and removing it from the plan.

        Args:
            work_id: ID of the planned work to execute.

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "work_id_required", "planned_work_not_found".
        """
        if not work_id:
            return {"status": "error", "message": "work_id_required"}

        planned_work = get_planned_work_func(work_id=work_id)
        if not planned_work:
            return {"status": "error", "message": "planned_work_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(planned_work), tool_context=tool_context)

        if confirmed:
            record_bonsai_event_func(
                bonsai_event=BonsaiEvent(
                    bonsai_id=planned_work.bonsai_id,
                    event_type=planned_work.work_type,
                    payload=planned_work.payload,
                )
            )
            delete_planned_work_func(work_id=work_id)
            return {"status": "success", "message": f"Planned work {work_id} executed and removed from plan."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_execute_planned_work
