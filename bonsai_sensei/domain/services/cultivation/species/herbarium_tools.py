from typing import Callable, Optional, List

from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_list_species_tool(get_all_species_func: Callable[[], list[dict]]):
    
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
                "common_name": item["common_name"],
                "scientific_name": item["scientific_name"],
            }
            for item in species_list
        ]
        return {"status": "success", "species": items}

    return list_bonsai_species


def create_get_species_by_name_tool(
    get_species_by_name_func: Callable[[str], Species | None],
):
    
    @limit_tool_calls(agent_name="botanist")
    def get_bonsai_species_by_name(name: str) -> dict:
        """Lookup a species by common name and return JSON with status and record.

        Args:
            name: Common name of the species.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","species":{"id","common_name","scientific_name","care_guide"}}.
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
                "care_guide": species.care_guide or {},
            },
        }

    return get_bonsai_species_by_name
