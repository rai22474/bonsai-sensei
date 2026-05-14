from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.pest import Pest
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_pest_tool(
    create_pest_func: Callable,
    get_pest_by_name_func: Callable[[str], Pest | None],
    wiki_page_builder: Callable[[str, str], str],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def create_pest(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a new pest in the catalog and generate its wiki page after user confirmation.

        Args:
            name: Pest name in Spanish, lowercase (e.g. 'araña roja').

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "pest_name_required", "pest_already_exists".
        """
        if not name:
            return {"status": "error", "message": "pest_name_required"}

        if get_pest_by_name_func(name):
            return {"status": "error", "message": "pest_already_exists"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)

        if confirmed:
            wiki_path = await wiki_page_builder(name)
            create_pest_func(pest=Pest(name=name, wiki_path=wiki_path))
            return {"status": "success", "message": f"Pest '{name}' registered."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return create_pest
