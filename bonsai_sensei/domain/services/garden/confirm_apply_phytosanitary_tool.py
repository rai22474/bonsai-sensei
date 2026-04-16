from typing import Callable

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_apply_phytosanitary_tool(
    get_bonsai_by_name_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    record_bonsai_event_func: Callable,
    ask_confirmation: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def confirm_apply_phytosanitary(
        bonsai_name: str,
        phytosanitary_name: str,
        amount: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Record a phytosanitary treatment on a bonsai after explicit user confirmation.

        Args:
            bonsai_name: Name of the bonsai that received the treatment.
            phytosanitary_name: Name of the phytosanitary product that was applied.
            amount: Amount of product applied (e.g. "5 ml", "10 g").
            summary: Human-readable description to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "phytosanitary_name_required", "amount_required",
                "bonsai_not_found", "phytosanitary_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not phytosanitary_name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if not amount:
            return {"status": "error", "message": "amount_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        phytosanitary = get_phytosanitary_by_name_func(phytosanitary_name)
        if not phytosanitary:
            return {"status": "error", "message": "phytosanitary_not_found"}

        confirmed = await ask_confirmation(summary, tool_context=tool_context)

        if confirmed:
            record_bonsai_event_func(
                bonsai_event=BonsaiEvent(
                    bonsai_id=bonsai.id,
                    event_type="phytosanitary_application",
                    payload={"phytosanitary_id": phytosanitary.id, "phytosanitary_name": phytosanitary_name, "amount": amount},
                )
            )
            return {"status": "success", "message": f"Phytosanitary '{phytosanitary_name}' treatment recorded on '{bonsai_name}'."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_apply_phytosanitary
