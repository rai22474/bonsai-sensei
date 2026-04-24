from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_update_phytosanitary_tool(
    update_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def confirm_update_phytosanitary(
        name: str,
        target: str | None = None,
        usage_sheet: str | None = None,
        recommended_amount: str | None = None,
        sources: list[str] | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Update a phytosanitary product in the catalog after explicit user confirmation.

        Args:
            name: Product name to update.
            target: Optional new target (pest/disease).
            usage_sheet: Optional new usage instructions.
            recommended_amount: Optional new recommended dosage amount.
            sources: Optional new list of source URLs.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "phytosanitary_name_required", "phytosanitary_not_found", "phytosanitary_update_required".
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if not get_phytosanitary_by_name_func(name):
            return {"status": "error", "message": "phytosanitary_not_found"}

        if target is None and usage_sheet is None and recommended_amount is None and sources is None:
            return {"status": "error", "message": "phytosanitary_update_required"}

        phytosanitary_data = {
            "usage_sheet": usage_sheet,
            "recommended_for": target,
            "recommended_amount": recommended_amount,
            "sources": sources,
        }

        confirmed = await ask_confirmation(build_confirmation_message(name, phytosanitary_data), tool_context=tool_context)

        if confirmed:
            update_phytosanitary_func(name=name, phytosanitary_data=phytosanitary_data)
            return {"status": "success", "message": f"Phytosanitary product '{name}' updated."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_update_phytosanitary
