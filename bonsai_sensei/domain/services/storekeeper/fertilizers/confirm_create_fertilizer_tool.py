from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_create_fertilizer_tool(
    create_fertilizer_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def confirm_create_fertilizer(
        name: str,
        usage_sheet: str,
        recommended_amount: str,
        summary: str,
        sources: list[str] | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to create a fertilizer and return JSON with care data.

        Args:
            name: Fertilizer name.
            usage_sheet: Usage instructions or full technical sheet text.
            recommended_amount: Recommended dosage string.
            summary: Short human-readable summary to show in the confirmation prompt.
            sources: Optional list of source URLs.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

            Output JSON (success): {"confirmation": <summary>}.
            Output JSON (error): {"status":"error","message":"..."}.
        """
        if sources is None:
            sources = []

        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if not usage_sheet:
            return {"status": "error", "message": "usage_sheet_required"}

        if not recommended_amount:
            return {"status": "error", "message": "recommended_amount_required"}
        if sources is None:
            sources = []

        command = Confirmation(
            id=uuid.uuid4().hex,
            summary=summary,
            executor=partial(
                create_fertilizer_func,
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                sources=sources,
            ),
        )
        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_create_fertilizer
