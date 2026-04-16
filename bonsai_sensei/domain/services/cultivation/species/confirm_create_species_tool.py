from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.species import Species


def create_confirm_create_species_tool(
    create_species_func: Callable,
    get_species_by_name_func: Callable[[str], Species | None],
    scientific_name_resolver: Callable[[str], dict],
    care_guide_builder: Callable[[str, str], dict],
    ask_confirmation: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def confirm_create_bonsai_species(
        common_name: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Create a new bonsai species with its scientific name and care guide after user confirmation.

        Resolves the scientific name and builds the care guide automatically using external sources.

        Args:
            common_name: Common name of the species to register.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "species_name_required", "species_already_exists", "scientific_name_not_found".
        """
        if not common_name:
            return {"status": "error", "message": "species_name_required"}

        if get_species_by_name_func(common_name):
            return {"status": "error", "message": "species_already_exists"}

        resolution = scientific_name_resolver(common_name)
        scientific_names = resolution.get("scientific_names", [])
        if not scientific_names:
            return {"status": "error", "message": "scientific_name_not_found"}

        scientific_name = scientific_names[0]
        care_guide = care_guide_builder(common_name, scientific_name)

        confirmed = await ask_confirmation(summary, tool_context=tool_context)

        if confirmed:
            create_species_func(
                Species(
                    name=common_name,
                    scientific_name=scientific_name,
                    care_guide=care_guide,
                )
            )
            return {"status": "success", "message": f"Species '{common_name}' created."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_create_bonsai_species
