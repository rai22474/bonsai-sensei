from typing import Callable

from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_get_species_by_name_tool(
    get_species_by_name_func: Callable[[str], Species | None],
):

    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    def get_bonsai_species_by_name(name: str) -> dict:
        """Lookup a species by common name and return JSON with status and record.

        Args:
            name: Common name of the species.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","species":{"id","common_name","scientific_name","wiki_path"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "species_name_required"}
        species = get_species_by_name_func(name)
        if not species:
            return {"status": "error", "message": "species_not_found"}
        return {
            "status": "success",
            "species": {
                "id": species.id,
                "common_name": species.name,
                "scientific_name": species.scientific_name or "",
                "wiki_path": species.wiki_path,
            },
        }

    return get_bonsai_species_by_name
