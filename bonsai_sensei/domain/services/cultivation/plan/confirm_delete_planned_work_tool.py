from functools import partial
from typing import Callable
import uuid

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_delete_planned_work_tool(
    get_planned_work_func: Callable,
    delete_planned_work_func: Callable,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="planning_agent")
    def confirm_delete_planned_work(
        planned_work_id: int,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to delete a planned work and return JSON with the result.

        Args:
            planned_work_id: ID of the planned work to delete.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "planned_work_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        work = get_planned_work_func(work_id=planned_work_id)
        if not work:
            return {"status": "error", "message": "planned_work_not_found"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(delete_planned_work_func, work_id=planned_work_id),
            deduplication_key=f"delete_planned_work:{planned_work_id}",
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_delete_planned_work
