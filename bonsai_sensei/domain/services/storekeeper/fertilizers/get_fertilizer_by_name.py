from pathlib import Path
from typing import Callable

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_get_fertilizer_by_name_tool(
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    wiki_root: str,
):
    wiki_root_path = Path(wiki_root).resolve()

    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def get_fertilizer_by_name(name: str) -> dict:
        """Look up a fertilizer and return its full technical sheet. Use when the user asks for details, specifications, or the ficha of a fertilizer. The 'content' field in the result contains the full wiki page and must be returned to the user as-is.

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
                "name": fertilizer.name.capitalize(),
                "recommended_amount": fertilizer.recommended_amount,
                "content": content,
            },
        }

    return get_fertilizer_by_name
