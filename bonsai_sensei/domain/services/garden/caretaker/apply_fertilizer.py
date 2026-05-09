from typing import Callable

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_apply_fertilizer_tool(
    get_bonsai_by_name_func: Callable,
    get_fertilizer_by_name_func: Callable,
    record_bonsai_event_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def apply_fertilizer(
        bonsai_name: str,
        fertilizer_name: str,
        amount: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Record a fertilizer application on a bonsai after explicit user confirmation.

        Args:
            bonsai_name: Name of the bonsai that received the fertilizer.
            fertilizer_name: Name of the fertilizer that was applied.
            amount: Amount of fertilizer applied (e.g. "5 ml", "10 g").

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "fertilizer_name_required", "amount_required",
                "bonsai_not_found", "fertilizer_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not fertilizer_name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if not amount:
            return {"status": "error", "message": "amount_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        fertilizer = get_fertilizer_by_name_func(fertilizer_name)
        if not fertilizer:
            return {"status": "error", "message": "fertilizer_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(bonsai_name, fertilizer_name, amount), tool_context=tool_context)

        if confirmed:
            record_bonsai_event_func(
                bonsai_event=BonsaiEvent(
                    bonsai_id=bonsai.id,
                    event_type="fertilizer_application",
                    payload={"fertilizer_id": fertilizer.id, "fertilizer_name": fertilizer_name, "amount": amount},
                )
            )
            return {"status": "success", "message": f"Fertilizer '{fertilizer_name}' application recorded on '{bonsai_name}'."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return apply_fertilizer
