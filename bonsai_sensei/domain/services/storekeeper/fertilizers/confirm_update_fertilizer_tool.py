from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_update_fertilizer_tool(
    update_fertilizer_func: Callable,
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def confirm_update_fertilizer(
        name: str,
        usage_sheet: str | None = None,
        recommended_amount: str | None = None,
        sources: list[str] | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Update a fertilizer in the catalog after explicit user confirmation.

        Args:
            name: Fertilizer name to update.
            usage_sheet: Optional new usage instructions.
            recommended_amount: Optional new recommended amount.
            sources: Optional new list of source URLs.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "fertilizer_name_required", "fertilizer_not_found", "fertilizer_update_required".
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if not get_fertilizer_by_name_func(name):
            return {"status": "error", "message": "fertilizer_not_found"}

        if usage_sheet is None and recommended_amount is None and sources is None:
            return {"status": "error", "message": "fertilizer_update_required"}

        fertilizer_data = {
            "usage_sheet": usage_sheet,
            "recommended_amount": recommended_amount,
            "sources": sources,
        }

        confirmed = await ask_confirmation(build_confirmation_message(name, fertilizer_data), tool_context=tool_context)

        if confirmed:
            update_fertilizer_func(name=name, fertilizer_data=fertilizer_data)
            return {"status": "success", "message": f"Fertilizer '{name}' updated."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_update_fertilizer
