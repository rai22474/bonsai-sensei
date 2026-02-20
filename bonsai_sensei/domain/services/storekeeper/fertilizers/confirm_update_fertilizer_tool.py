from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_update_fertilizer_tool(
    update_fertilizer_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def confirm_update_fertilizer(
        name: str,
        summary: str,
        usage_sheet: str | None = None,
        recommended_amount: str | None = None,
        sources: list[str] | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to update a fertilizer and return JSON with the planned changes.

        Args:
            name: Fertilizer name to update.
            summary: Short human-readable summary to show in the confirmation prompt.
            usage_sheet: Optional new usage instructions.
            recommended_amount: Optional new recommended amount.
            sources: Optional new list of source URLs.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"confirmation": <summary>}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "fertilizer_name_required",
            "fertilizer_update_required".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if usage_sheet is None and recommended_amount is None and sources is None:
            return {"status": "error", "message": "fertilizer_update_required"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                update_fertilizer_func,
                name=name,
                fertilizer_data={
                    "usage_sheet": usage_sheet,
                    "recommended_amount": recommended_amount,
                    "sources": sources,
                },
            ),
        )

        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_update_fertilizer
