from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import _extract_recommended_amount


def create_confirm_create_fertilizer_tool(
    create_fertilizer_func: Callable,
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    searcher: Callable[[str], dict],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def confirm_create_fertilizer(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Search for the fertilizer guide online and create it after user confirmation.

        Args:
            name: Fertilizer name.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "fertilizer_name_required", "fertilizer_already_exists".
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if get_fertilizer_by_name_func(name):
            return {"status": "error", "message": "fertilizer_already_exists"}

        search_response = searcher(f"{name} bonsai dosis de uso ficha tecnica fertilizante")
        answer = str(search_response.get("answer", "")).strip()
        sources = [str(item.get("url")) for item in search_response.get("results", []) if item.get("url")]
        usage_sheet = answer or "No data available."
        recommended_amount = _extract_recommended_amount(answer)

        confirmed = await ask_confirmation(build_confirmation_message(name, usage_sheet, recommended_amount), tool_context=tool_context)

        if confirmed:
            create_fertilizer_func(
                fertilizer=Fertilizer(
                    name=name,
                    usage_sheet=usage_sheet,
                    recommended_amount=recommended_amount,
                    sources=sources,
                )
            )
            return {"status": "success", "message": f"Fertilizer '{name}' created."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_create_fertilizer
