from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.services.storekeeper.phytosanitary.phytosanitary_tools import _extract_recommended_amount


def create_confirm_create_phytosanitary_tool(
    create_phytosanitary_func: Callable,
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
    searcher: Callable[[str], dict],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    async def confirm_create_phytosanitary(
        name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Search for the phytosanitary product guide online and create it after user confirmation.

        Args:
            name: Product name.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "phytosanitary_name_required", "phytosanitary_already_exists".
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if get_phytosanitary_by_name_func(name):
            return {"status": "error", "message": "phytosanitary_already_exists"}

        search_response = searcher(f"{name} bonsai dosis de uso ficha tecnica fitosanitario")
        answer = str(search_response.get("answer", "")).strip()
        sources = [str(item.get("url")) for item in search_response.get("results", []) if item.get("url")]
        usage_sheet = answer or "No data available."
        recommended_amount = _extract_recommended_amount(answer)
        recommended_for = "Plagas comunes"

        confirmed = await ask_confirmation(build_confirmation_message(name, usage_sheet, recommended_amount), tool_context=tool_context)

        if confirmed:
            create_phytosanitary_func(
                phytosanitary=Phytosanitary(
                    name=name,
                    usage_sheet=usage_sheet,
                    recommended_amount=recommended_amount,
                    recommended_for=recommended_for,
                    sources=sources,
                )
            )
            return {"status": "success", "message": f"Phytosanitary product '{name}' created."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_create_phytosanitary
