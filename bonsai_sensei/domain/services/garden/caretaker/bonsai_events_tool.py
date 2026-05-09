from typing import Callable

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_bonsai_events_tool(
    get_bonsai_by_name_func: Callable[[str], Bonsai | None],
    list_bonsai_events_func: Callable[[int], list[dict]],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    def list_bonsai_events(bonsai_name: str) -> dict:
        """List all recorded events for a bonsai by name and return JSON with status and events.

        Args:
            bonsai_name: Name of the bonsai to retrieve events for.

        Returns:
            A JSON-ready dictionary with the event list.

        Output JSON (success): {"status": "success", "events": [{"id", "event_type", "payload", "occurred_at"}]}.
        Output JSON (error): {"status": "error", "message": "..."}.
        Error reasons: "bonsai_name_required", "bonsai_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}
        events = list_bonsai_events_func(bonsai_id=bonsai.id)
        return {"status": "success", "events": events}

    return list_bonsai_events
