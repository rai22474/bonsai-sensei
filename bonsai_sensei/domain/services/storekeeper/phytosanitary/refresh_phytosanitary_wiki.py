from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_refresh_phytosanitary_wiki_tool(
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    update_phytosanitary_func: Callable,
    wiki_page_builder: Callable[[str], tuple[str, str]],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def refresh_phytosanitary_wiki(
        name: str,
        instructions: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Regenerate the wiki page for a phytosanitary product from updated online sources.

        Args:
            name: Phytosanitary product name whose wiki page should be refreshed.
            instructions: Optional user instructions about what to improve or focus on
                (e.g. 'amplía la sección de plagas objetivo').

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "phytosanitary_name_required", "phytosanitary_not_found".
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if not get_phytosanitary_by_name_func(name):
            return {"status": "error", "message": "phytosanitary_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)
        if not confirmed:
            return {"status": "cancelled", "reason": confirmed.reason}

        wiki_path, recommended_amount = await wiki_page_builder(name, instructions)
        update_phytosanitary_func(name=name, phytosanitary_data={"wiki_path": wiki_path, "recommended_amount": recommended_amount})
        return {"status": "success", "message": f"Wiki page for '{name}' has been refreshed."}

    return refresh_phytosanitary_wiki
