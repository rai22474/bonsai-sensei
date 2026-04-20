from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_delete_bonsai_tool(
    delete_bonsai_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def confirm_delete_bonsai(
        bonsai_id: int,
        bonsai_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a bonsai from the collection after explicit user confirmation.

        Asks the user to confirm before executing the deletion. If confirmed,
        the bonsai is permanently removed. If declined, no action is taken.

        Args:
            bonsai_id: Identifier of the bonsai to delete.
            bonsai_name: Name of the bonsai to delete.

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_id_required", "bonsai_name_required".
        """
        if not bonsai_id:
            return {"status": "error", "message": "bonsai_id_required"}
        
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        confirmed = await ask_confirmation(build_confirmation_message(bonsai_id, bonsai_name), tool_context=tool_context)

        if confirmed:
            delete_bonsai_func(bonsai_id=bonsai_id)
            return {"status": "success", "message": f"Bonsai '{bonsai_name}' deleted."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_delete_bonsai
