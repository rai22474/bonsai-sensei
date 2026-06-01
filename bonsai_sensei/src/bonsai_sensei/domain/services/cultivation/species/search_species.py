from typing import Callable

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_search_species_tool(
    search_species_func: Callable[[str], list],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    def search_bonsai_species(query: str) -> dict:
        """Search species in the herbarium by partial common or scientific name.

        Use this to find a species and obtain its wiki_path before reading its care guide.

        Args:
            query: Partial common or scientific name to search for.

        Returns:
            A JSON-ready dictionary with matching species.
            Output JSON: {"status": "success", "species": [{"common_name", "scientific_name", "wiki_path"}, ...]}.
            Output JSON (no results): {"status": "success", "species": []}.
        """
        results = search_species_func(query)
        return {
            "status": "success",
            "species": [
                {
                    "common_name": species.name.capitalize(),
                    "scientific_name": species.scientific_name or "",
                    "wiki_path": species.wiki_path or "",
                }
                for species in results
            ],
        }

    return search_bonsai_species
