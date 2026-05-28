from typing import Callable

from bonsai_sensei.domain.pest import Pest
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_pests_tool(list_pests_func: Callable[[], list[Pest]]):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    def list_pests() -> dict:
        """Return all pests registered in the catalog.

        Returns:
            A JSON-ready dictionary with the pest list.

        Output JSON: {"status": "success", "pests": [{"id", "name", "wiki_path"}]}.
        """
        items = list_pests_func()
        return {
            "status": "success",
            "pests": [{"id": pest.id, "name": pest.name.capitalize(), "wiki_path": pest.wiki_path} for pest in items],
        }

    return list_pests
