from pathlib import Path
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
                "name": fertilizer.name,
            }
            for fertilizer in fertilizers
        ]
        return {"status": "success", "fertilizers": items}

    return list_fertilizers


def create_get_fertilizer_by_name_tool(
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    wiki_root: str,
):
    wiki_root_path = Path(wiki_root).resolve()

    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def get_fertilizer_by_name(name: str) -> dict:
        """Lookup a fertilizer by name and return its full wiki page content.

        Args:
            name: Fertilizer name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","fertilizer":{"id","name","recommended_amount","content":"<markdown>"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        fertilizer = get_fertilizer_by_name_func(name)
        if not fertilizer:
            return {"status": "error", "message": "fertilizer_not_found"}
        content = None
        if fertilizer.wiki_path:
            page_path = (wiki_root_path / fertilizer.wiki_path).resolve()
            if str(page_path).startswith(str(wiki_root_path)) and page_path.exists():
                content = page_path.read_text(encoding="utf-8")
        return {
            "status": "success",
            "fertilizer": {
                "id": fertilizer.id,
                "name": fertilizer.name,
                "recommended_amount": fertilizer.recommended_amount,
                "content": content,
            },
        }

    return get_fertilizer_by_name
