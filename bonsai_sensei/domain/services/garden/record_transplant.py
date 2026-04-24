from typing import Callable

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_record_transplant_tool(
    get_bonsai_by_name_func: Callable,
    record_bonsai_event_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def confirm_record_transplant(
        bonsai_name: str,
        pot_size: str,
        pot_type: str,
        substrate: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Record a transplant event on a bonsai after explicit user confirmation.

        Args:
            bonsai_name: Name of the bonsai that was transplanted.
            pot_size: Size of the new pot (e.g. "20 cm", "small").
            pot_type: Type/material of the new pot (e.g. "cerámica", "plástico", "mica").
            substrate: Substrate used in the transplant (e.g. "akadama y pomice").

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "bonsai_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        payload = {key: value for key, value in {"pot_size": pot_size, "pot_type": pot_type, "substrate": substrate}.items() if value}

        confirmed = await ask_confirmation(build_confirmation_message(bonsai_name, pot_size, pot_type, substrate), tool_context=tool_context)

        if confirmed:
            record_bonsai_event_func(
                bonsai_event=BonsaiEvent(
                    bonsai_id=bonsai.id,
                    event_type="transplant",
                    payload=payload,
                )
            )
            return {"status": "success", "message": f"Transplant recorded for '{bonsai_name}'."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_record_transplant
