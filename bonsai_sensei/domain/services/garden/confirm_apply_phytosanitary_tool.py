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


def create_confirm_apply_phytosanitary_tool(
    get_bonsai_by_name_func,
    get_phytosanitary_by_name_func,
    record_bonsai_event_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="gardener")
    def confirm_apply_phytosanitary(
        bonsai_name: str,
        phytosanitary_name: str,
        amount: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to record a phytosanitary treatment on a bonsai.

        Args:
            bonsai_name: Name of the bonsai that received the treatment.
            phytosanitary_name: Name of the phytosanitary product that was applied.
            amount: Amount of product applied (e.g. "5 ml", "10 g").
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "bonsai_name_required",
            "phytosanitary_name_required", "amount_required", "bonsai_not_found", "phytosanitary_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not phytosanitary_name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if not amount:
            return {"status": "error", "message": "amount_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        phytosanitary = get_phytosanitary_by_name_func(phytosanitary_name)
        if not phytosanitary:
            return {"status": "error", "message": "phytosanitary_not_found"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                record_bonsai_event_func,
                bonsai_event=BonsaiEvent(
                    bonsai_id=bonsai.id,
                    event_type="phytosanitary_application",
                    payload={"phytosanitary_name": phytosanitary_name, "amount": amount},
                ),
            ),
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_apply_phytosanitary
