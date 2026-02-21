from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_update_phytosanitary_tool(
    update_phytosanitary_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def confirm_update_phytosanitary(
        name: str,
        summary: str,
        target: str | None = None,
        usage_sheet: str | None = None,
        recommended_amount: str | None = None,
        sources: list[str] | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to update a phytosanitary product and return JSON with planned changes.

        Args:
            name: Product name to update.
            summary: Short human-readable summary to show in the confirmation prompt.
            target: Optional new target (pest/disease).
            usage_sheet: Optional new usage instructions.
            recommended_amount: Optional new recommended dosage amount.
            sources: Optional new list of source URLs.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "phytosanitary_name_required",
            "phytosanitary_update_required".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if target is None and usage_sheet is None and recommended_amount is None and sources is None:
            return {"status": "error", "message": "phytosanitary_update_required"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                update_phytosanitary_func,
                name=name,
                phytosanitary_data={
                    "usage_sheet": usage_sheet,
                    "recommended_for": target,
                    "recommended_amount": recommended_amount,
                    "sources": sources,
                },
            ),
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_update_phytosanitary
