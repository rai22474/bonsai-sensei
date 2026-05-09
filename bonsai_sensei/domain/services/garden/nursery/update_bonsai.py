from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_update_bonsai_tool(
    update_bonsai_func: Callable,
    get_species_by_name_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def update_bonsai(
        bonsai_id: int,
        bonsai_name: str,
        name: str | None = None,
        species_name: str | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Update a bonsai in the collection after explicit user confirmation.

        Args:
            bonsai_id: Identifier of the bonsai to update.
            bonsai_name: Current name of the bonsai to update.
            name: Optional new name for the bonsai.
            species_name: Optional common name of the new species to assign.

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_id_required", "bonsai_name_required", "species_not_found", "bonsai_update_required".
        """
        if not bonsai_id:
            return {"status": "error", "message": "bonsai_id_required"}

        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        bonsai_data = {}
        if name is not None:
            bonsai_data["name"] = name

        if species_name is not None:
            species = get_species_by_name_func(species_name)
            if not species:
                return {"status": "error", "message": "species_not_found"}
            bonsai_data["species_id"] = species.id

        if not bonsai_data:
            return {"status": "error", "message": "bonsai_update_required"}

        confirmed = await ask_confirmation(build_confirmation_message(bonsai_id, bonsai_name, bonsai_data), tool_context=tool_context)

        if confirmed:
            update_bonsai_func(bonsai_id=bonsai_id, bonsai_data=bonsai_data)
            return {"status": "success", "message": f"Bonsai '{bonsai_name}' updated."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return update_bonsai
