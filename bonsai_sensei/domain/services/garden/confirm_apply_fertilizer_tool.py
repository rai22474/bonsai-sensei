from functools import partial
import uuid
from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_apply_fertilizer_tool(
    get_bonsai_by_name_func,
    get_fertilizer_by_name_func,
    record_bonsai_event_func,
    confirmation_store: ConfirmationStore,
):

    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    def confirm_apply_fertilizer(
        bonsai_name: str,
        fertilizer_name: str,
        amount: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to record a fertilizer application on a bonsai.

        Args:
            bonsai_name: Name of the bonsai that received the fertilizer.
            fertilizer_name: Name of the fertilizer that was applied.
            amount: Amount of fertilizer applied (e.g. "5 ml", "10 g").
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "bonsai_name_required",
            "fertilizer_name_required", "amount_required", "bonsai_not_found", "fertilizer_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not fertilizer_name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if not amount:
            return {"status": "error", "message": "amount_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        fertilizer = get_fertilizer_by_name_func(fertilizer_name)
        if not fertilizer:
            return {"status": "error", "message": "fertilizer_not_found"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                record_bonsai_event_func,
                bonsai_event=BonsaiEvent(
                    bonsai_id=bonsai.id,
                    event_type="fertilizer_application",
                    payload={"fertilizer_id": fertilizer.id, "fertilizer_name": fertilizer_name, "amount": amount},
                ),
            ),
            deduplication_key=f"apply_fertilizer:{bonsai_name}:{fertilizer_name}",
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_apply_fertilizer
