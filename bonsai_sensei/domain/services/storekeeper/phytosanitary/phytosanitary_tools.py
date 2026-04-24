from typing import Callable

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_phytosanitary_tool(
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def list_phytosanitary() -> dict:
        """Return JSON with all registered phytosanitary items.

        Returns:
            A JSON-ready dictionary with the phytosanitary list.

        Output JSON: {"status":"success","phytosanitary":[{"id","name","recommended_amount","wiki_path"}]}.
        """
        items = list_phytosanitary_func()
        results = [
            {
                "id": phytosanitary.id,
                "name": phytosanitary.name,
                "recommended_amount": phytosanitary.recommended_amount,
                "wiki_path": phytosanitary.wiki_path,
            }
            for phytosanitary in items
        ]
        return {"status": "success", "phytosanitary": results}

    return list_phytosanitary


def create_get_phytosanitary_by_name_tool(
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def get_phytosanitary_by_name(name: str) -> dict:
        """Lookup a phytosanitary by name and return JSON with status and record.

        Args:
            name: Phytosanitary name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","phytosanitary":{"id","name","recommended_amount","wiki_path"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        phytosanitary = get_phytosanitary_by_name_func(name)
        if not phytosanitary:
            return {"status": "error", "message": "phytosanitary_not_found"}
        return {
            "status": "success",
            "phytosanitary": {
                "id": phytosanitary.id,
                "name": phytosanitary.name,
                "recommended_amount": phytosanitary.recommended_amount,
                "wiki_path": phytosanitary.wiki_path,
            },
        }

    return get_phytosanitary_by_name
