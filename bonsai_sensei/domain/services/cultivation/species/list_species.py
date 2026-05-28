from typing import Callable

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_species_tool(get_all_species_func: Callable[[], list[dict]]):

    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    def list_bonsai_species() -> dict:
        """Return a JSON payload with the list of known species.

        The returned dictionary is suitable for agent consumption and is
        intentionally simple (JSON-serializable). When there are no
        species the `species` key contains an empty list.

        Returns:
            A dict with the shape:
            {
                "status": "success",
                "species": [
                    {"common_name": str, "scientific_name": str},
                    ...
                ]
            }
        """
        species_list = get_all_species_func()
        if not species_list:
            return {"status": "success", "species": []}
        items = [
            {
                "common_name": item["common_name"].capitalize(),
                "scientific_name": item["scientific_name"],
            }
            for item in species_list
        ]
        return {"status": "success", "species": items}

    return list_bonsai_species
