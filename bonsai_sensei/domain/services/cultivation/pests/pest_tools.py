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
            "pests": [{"id": pest.id, "name": pest.name, "wiki_path": pest.wiki_path} for pest in items],
        }

    return list_pests


def create_get_pest_by_name_tool(get_pest_by_name_func: Callable[[str], Pest | None]):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    def get_pest_by_name(name: str) -> dict:
        """Look up a pest by name.

        Args:
            name: Pest name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status": "success", "pest": {"id", "name", "wiki_path"}}.
        Output JSON (error): {"status": "error", "message": "pest_not_found"}.
        """
        if not name:
            return {"status": "error", "message": "pest_name_required"}
        pest = get_pest_by_name_func(name)
        if not pest:
            return {"status": "error", "message": "pest_not_found"}
        return {"status": "success", "pest": {"id": pest.id, "name": pest.name, "wiki_path": pest.wiki_path}}

    return get_pest_by_name
