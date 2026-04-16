from typing import Callable

from bonsai_sensei.domain.bonsai import Bonsai
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_create_bonsai_tool(
    create_bonsai_func: Callable,
    get_species_by_name_func: Callable,
    ask_confirmation: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def confirm_create_bonsai(
        name: str,
        species_name: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Create a new bonsai in the collection after explicit user confirmation.

        Args:
            name: Bonsai name.
            species_name: Common name of the species to assign to the bonsai.
            summary: Human-readable description to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "species_name_required", "species_not_found".
        """
        if not name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not species_name:
            return {"status": "error", "message": "species_name_required"}

        species = get_species_by_name_func(species_name)
        if not species:
            return {"status": "error", "message": "species_not_found"}

        confirmed = await ask_confirmation(summary, tool_context=tool_context)

        if confirmed:
            create_bonsai_func(bonsai=Bonsai(name=name, species_id=species.id))
            return {"status": "success", "message": f"Bonsai '{name}' created."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_create_bonsai
