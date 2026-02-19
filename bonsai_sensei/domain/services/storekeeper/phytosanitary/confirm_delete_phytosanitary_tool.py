from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_delete_phytosanitary_tool(
    delete_phytosanitary_func,
    confirmation_store: ConfirmationStore,
):
    
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def confirm_delete_phytosanitary(
        name: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to delete a phytosanitary product and return JSON with the result.

        Args:
            name: Product name to delete.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"confirmation": True, "summary": <summary>, "registered": True}.
        Output JSON (error): {"status":"error","message":"..."}.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            summary=summary,
            executor=partial(
                delete_phytosanitary_func,
                name=name,
            ),
        )
        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_delete_phytosanitary
