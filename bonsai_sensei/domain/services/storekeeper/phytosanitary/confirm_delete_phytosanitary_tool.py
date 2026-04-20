from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_delete_phytosanitary_tool(
    delete_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def confirm_delete_phytosanitary(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a phytosanitary product from the catalog after explicit user confirmation.

        Args:
            name: Product name to delete.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "phytosanitary_name_required", "phytosanitary_not_found".
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if not get_phytosanitary_by_name_func(name):
            return {"status": "error", "message": "phytosanitary_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)

        if confirmed:
            delete_phytosanitary_func(name=name)
            return {"status": "success", "message": f"Phytosanitary product '{name}' deleted."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_delete_phytosanitary
