from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_refresh_fertilizer_wiki_tool(
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    update_fertilizer_func: Callable,
    wiki_page_builder: Callable[[str], tuple[str, str]],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def refresh_fertilizer_wiki(
        name: str,
        instructions: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Regenerate the wiki page for a fertilizer from updated online sources.

        Args:
            name: Fertilizer name whose wiki page should be refreshed.
            instructions: Optional user instructions about what to improve or focus on
                (e.g. 'añade información sobre aplicación en otoño').

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "fertilizer_name_required", "fertilizer_not_found".
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if not get_fertilizer_by_name_func(name):
            return {"status": "error", "message": "fertilizer_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)
        if not confirmed:
            return {"status": "cancelled", "reason": confirmed.reason}

        wiki_path, recommended_amount = await wiki_page_builder(name, instructions)
        update_fertilizer_func(name=name, fertilizer_data={"wiki_path": wiki_path, "recommended_amount": recommended_amount})
        return {"status": "success", "message": f"Wiki page for '{name}' has been refreshed."}

    return refresh_fertilizer_wiki
