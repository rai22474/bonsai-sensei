from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_update_species_tool(
    update_species_func: Callable,
    get_species_by_name_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def confirm_update_species(
        species: dict,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Update a species in the herbarium after explicit user confirmation.

        Args:
            species: A mapping with fields to update. Use 'name' or 'common_name' to
                identify the species to update. Use 'common_name' to rename it and
                'scientific_name' to update its scientific name.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "species_name_required", "species_update_required", "species_not_found".
        """
        species_name = species.get("name") or species.get("common_name")
        if not species_name:
            return {"status": "error", "message": "species_name_required"}

        common_name = species.get("common_name")
        scientific_name = species.get("scientific_name")

        species_data = {}
        if common_name is not None:
            species_data["name"] = common_name
        if scientific_name is not None:
            species_data["scientific_name"] = scientific_name

        if not species_data:
            return {"status": "error", "message": "species_update_required"}

        existing_species = get_species_by_name_func(species_name)
        if not existing_species:
            return {"status": "error", "message": "species_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(species_name, species_data), tool_context=tool_context)

        if confirmed:
            update_species_func(species_id=existing_species.id, species_data=species_data)
            return {"status": "success", "message": f"Species '{species_name}' updated."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_update_species
