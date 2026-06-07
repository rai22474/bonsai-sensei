from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_phytosanitary_tool(
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def list_phytosanitary(tool_context: ToolContext | None = None) -> dict:
        """Return JSON with all registered phytosanitary items.

        Returns:
            A JSON-ready dictionary with the phytosanitary list.

        Output JSON: {"status":"success","phytosanitary":[{"id","name"}]}.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        items = list_phytosanitary_func(user_id=user_id)
        results = [
            {
                "id": phytosanitary.id,
                "name": phytosanitary.name.capitalize(),
            }
            for phytosanitary in items
        ]
        return {"status": "success", "phytosanitary": results}

    return list_phytosanitary
