from pathlib import Path
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

        Output JSON: {"status":"success","phytosanitary":[{"id","name"}]}.
        """
        items = list_phytosanitary_func()
        results = [
            {
                "id": phytosanitary.id,
                "name": phytosanitary.name,
            }
            for phytosanitary in items
        ]
        return {"status": "success", "phytosanitary": results}

    return list_phytosanitary


def create_get_phytosanitary_by_name_tool(
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    wiki_root: str,
):
    wiki_root_path = Path(wiki_root).resolve()

    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def get_phytosanitary_by_name(name: str) -> dict:
        """Lookup a phytosanitary product by name and return its full wiki page content.

        Args:
            name: Phytosanitary name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","phytosanitary":{"id","name","recommended_amount","content":"<markdown>"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        phytosanitary = get_phytosanitary_by_name_func(name)
        if not phytosanitary:
            return {"status": "error", "message": "phytosanitary_not_found"}
        content = None
        if phytosanitary.wiki_path:
            page_path = (wiki_root_path / phytosanitary.wiki_path).resolve()
            if str(page_path).startswith(str(wiki_root_path)) and page_path.exists():
                content = page_path.read_text(encoding="utf-8")
        return {
            "status": "success",
            "phytosanitary": {
                "id": phytosanitary.id,
                "name": phytosanitary.name,
                "recommended_amount": phytosanitary.recommended_amount,
                "content": content,
            },
        }

    return get_phytosanitary_by_name
