from typing import Callable

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_fertilizers_tool(list_fertilizers_func: Callable[[], list[Fertilizer]]):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def list_fertilizers() -> dict:
        """Return JSON with all registered fertilizers.

        Returns:
            A JSON-ready dictionary with the fertilizer list.

        Output JSON: {"status":"success","fertilizers":[{"id","name"}]}.
        """
        fertilizers = list_fertilizers_func()
        items = [
            {
                "id": fertilizer.id,
                "name": fertilizer.name.capitalize(),
            }
            for fertilizer in fertilizers
        ]
        return {"status": "success", "fertilizers": items}

    return list_fertilizers
