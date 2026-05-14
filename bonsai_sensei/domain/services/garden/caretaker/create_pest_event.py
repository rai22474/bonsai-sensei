from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_pest_event_tool(
    get_bonsai_by_name_func: Callable,
    get_pest_by_name_func: Callable,
    record_bonsai_event_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="caretaker")
    async def create_pest_event(
        bonsai_name: str,
        pest_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Record a pest detection event on a bonsai after explicit user confirmation.

        Args:
            bonsai_name: Name of the bonsai where the pest was detected.
            pest_name: Name of the pest detected (must be registered in the catalog).

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "pest_name_required",
                "bonsai_not_found", "pest_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not pest_name:
            return {"status": "error", "message": "pest_name_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        pest = get_pest_by_name_func(pest_name)
        if not pest:
            return {"status": "error", "message": "pest_not_found"}

        confirmed = await ask_confirmation(
            build_confirmation_message(bonsai_name, pest_name),
            tool_context=tool_context,
        )

        if confirmed:
            record_bonsai_event_func(
                bonsai_event=BonsaiEvent(
                    bonsai_id=bonsai.id,
                    event_type="pest_detection",
                    payload={"pest_id": pest.id, "pest_name": pest_name},
                )
            )
            return {"status": "success", "message": f"Pest detection of '{pest_name}' recorded on '{bonsai_name}'."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return create_pest_event
