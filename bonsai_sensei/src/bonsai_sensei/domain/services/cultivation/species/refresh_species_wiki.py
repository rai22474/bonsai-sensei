from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_refresh_species_wiki_tool(
    get_species_by_name_func: Callable[[str], Species | None],
    update_species_func: Callable,
    wiki_page_builder: Callable[[str, str], str],
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def refresh_species_wiki(
        name: str,
        instructions: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Regenerate the wiki care guide for a species from updated online sources.

        Args:
            name: Common name of the species whose wiki page should be refreshed.
            instructions: Optional user instructions about what to improve or focus on
                (e.g. 'profundiza en los cuidados por estación').

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "species_name_required", "species_not_found".
        """
        if not name:
            return {"status": "error", "message": "species_name_required"}

        species = get_species_by_name_func(name)
        if not species:
            return {"status": "error", "message": "species_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name), tool_context=tool_context)
        if not confirmed:
            return {"status": "cancelled", "reason": confirmed.reason}

        wiki_path = await wiki_page_builder(species.name, species.scientific_name, instructions)
        update_species_func(species_id=species.id, species_data={"wiki_path": wiki_path})
        return {"status": "success", "message": f"Wiki page for '{name}' has been refreshed."}

    return refresh_species_wiki
