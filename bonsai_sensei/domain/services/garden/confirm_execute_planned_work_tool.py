import uuid

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_execute_planned_work_tool(
    get_planned_work_func,
    record_bonsai_event_func,
    delete_planned_work_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="gardener")
    def confirm_execute_planned_work(
        work_id: int,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to execute a planned work, recording a bonsai event and removing it from the plan.

        Args:
            work_id: ID of the planned work to execute.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "work_id_required", "planned_work_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not work_id:
            return {"status": "error", "message": "work_id_required"}

        planned_work = get_planned_work_func(work_id=work_id)
        if not planned_work:
            return {"status": "error", "message": "planned_work_not_found"}

        captured_work_id = work_id
        captured_bonsai_id = planned_work.bonsai_id
        captured_work_type = planned_work.work_type
        captured_payload = planned_work.payload

        def execute_work():
            record_bonsai_event_func(
                bonsai_event=BonsaiEvent(
                    bonsai_id=captured_bonsai_id,
                    event_type=captured_work_type,
                    payload=captured_payload,
                )
            )
            delete_planned_work_func(work_id=captured_work_id)

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=execute_work,
            deduplication_key=f"execute_planned_work:{work_id}",
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_execute_planned_work
