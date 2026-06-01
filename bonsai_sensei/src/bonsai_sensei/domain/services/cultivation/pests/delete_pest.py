from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.pest import Pest
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_delete_pest_tool(
    delete_pest_func: Callable,
    get_pest_by_name_func: Callable[[str], Pest | None],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def delete_pest(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a pest from the catalog after explicit user confirmation.

        Args:
            name: Pest name to delete.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "pest_name_required", "pest_not_found".
        """
        if not name:
            return {"status": "error", "message": "pest_name_required"}

        if not get_pest_by_name_func(name):
            return {"status": "error", "message": "pest_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)

        if confirmed:
            delete_pest_func(name=name)
            return {"status": "success", "message": f"Pest '{name}' deleted."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return delete_pest
