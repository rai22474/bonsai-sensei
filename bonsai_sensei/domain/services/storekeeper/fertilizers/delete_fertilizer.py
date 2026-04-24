from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_delete_fertilizer_tool(
    delete_fertilizer_func: Callable,
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def confirm_delete_fertilizer(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a fertilizer from the catalog after explicit user confirmation.

        Args:
            name: Fertilizer name to delete.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "fertilizer_name_required", "fertilizer_not_found".
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if not get_fertilizer_by_name_func(name):
            return {"status": "error", "message": "fertilizer_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)

        if confirmed:
            delete_fertilizer_func(name=name)
            return {"status": "success", "message": f"Fertilizer '{name}' deleted."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_delete_fertilizer
