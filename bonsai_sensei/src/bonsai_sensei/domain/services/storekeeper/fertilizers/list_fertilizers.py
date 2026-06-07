from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_fertilizers_tool(list_fertilizers_func: Callable[[], list[Fertilizer]]):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def list_fertilizers(tool_context: ToolContext | None = None) -> dict:
        """Return JSON with all registered fertilizers.

        Returns:
            A JSON-ready dictionary with the fertilizer list.

        Output JSON: {"status":"success","fertilizers":[{"id","name"}]}.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        fertilizers = list_fertilizers_func(user_id=user_id)
        items = [
            {
                "id": fertilizer.id,
                "name": fertilizer.name.capitalize(),
            }
            for fertilizer in fertilizers
        ]
        return {"status": "success", "fertilizers": items}

    return list_fertilizers
