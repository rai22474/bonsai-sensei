from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_delete_species_tool(
    delete_species_func: Callable,
    get_species_by_name_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def confirm_delete_species(
        species_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a species from the herbarium after explicit user confirmation.

        Args:
            species_name: The common name of the species to delete.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "species_name_required", "species_not_found".
        """
        if not species_name:
            return {"status": "error", "message": "species_name_required"}

        existing_species = get_species_by_name_func(species_name)
        if not existing_species:
            return {"status": "error", "message": "species_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(species_name), tool_context=tool_context)

        if confirmed:
            delete_species_func(species_id=existing_species.id)
            return {"status": "success", "message": f"Species '{species_name}' deleted."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_delete_species
