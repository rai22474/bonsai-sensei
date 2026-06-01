from typing import Callable

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.infrastructure.wiki_client import create_http_read_wiki_page_tool


def create_get_phytosanitary_by_name_tool(
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    kb_base_url: str = "",
    wiki_root: str = "",
):
    read_wiki = create_http_read_wiki_page_tool(kb_base_url or wiki_root)

    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def get_phytosanitary_by_name(name: str) -> dict:
        """Look up a phytosanitary product and return its full technical sheet. Use when the user asks for details, specifications, or the ficha of a phytosanitary product. The 'content' field in the result contains the full wiki page and must be returned to the user as-is.

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
            result = read_wiki(path=phytosanitary.wiki_path)
            content = result.get("content", "") if result.get("status") == "success" else None
        return {
            "status": "success",
            "phytosanitary": {
                "id": phytosanitary.id,
                "name": phytosanitary.name.capitalize(),
                "recommended_amount": phytosanitary.recommended_amount,
                "content": content,
            },
        }

    return get_phytosanitary_by_name
