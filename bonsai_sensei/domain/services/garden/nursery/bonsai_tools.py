from typing import Callable

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_list_bonsai_tool(
    list_bonsai_func: Callable[[], list[Bonsai]],
    list_species_func: Callable[[], list[Species]],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="nursery")
    def list_bonsai() -> dict:
        """Return JSON with status and bonsai list.

        Returns:
            A JSON-ready dictionary with the bonsai list.

        Output JSON: {"status": "success", "bonsai": [{"id","name","species_id","species_name"}]}.
        """
        bonsai_items = list_bonsai_func()
        if not bonsai_items:
            return {"status": "success", "bonsai": []}
        species_map = _build_species_map(list_species_func())
        items = [
            _build_bonsai_dict(bonsai, species_map)
            for bonsai in bonsai_items
        ]
        return {"status": "success", "bonsai": items}

    return list_bonsai


def create_get_bonsai_by_name_tool(
    get_bonsai_by_name_func: Callable[[str], Bonsai | None],
    list_species_func: Callable[[], list[Species]],
):
    @trace_tool_call
    @limit_tool_calls(agent_name="nursery")
    def get_bonsai_by_name(name: str) -> dict:
        """Lookup a bonsai by name and return JSON with status and record.

        Args:
            name: Bonsai name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","bonsai":{"id","name","species_id","species_name"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "bonsai_name_required"}
        bonsai = get_bonsai_by_name_func(name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}
        species_map = _build_species_map(list_species_func())
        return {"status": "success", "bonsai": _build_bonsai_dict(bonsai, species_map)}

    return get_bonsai_by_name


def _build_species_map(species_items: list[Species]) -> dict[int, Species]:
    return {species.id: species for species in species_items if species.id is not None}


def _build_bonsai_dict(bonsai: Bonsai, species_map: dict[int, Species]) -> dict:
    species = species_map.get(bonsai.species_id)
    return {
        "id": bonsai.id,
        "name": bonsai.name.capitalize(),
        "species_id": bonsai.species_id,
        "species_name": species.name.capitalize() if species else f"Especie {bonsai.species_id}",
        "species_emoji": species.get_emoji() if species else "🌱",
    }
