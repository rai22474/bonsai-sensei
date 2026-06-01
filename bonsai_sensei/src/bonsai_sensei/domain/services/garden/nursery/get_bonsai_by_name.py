from typing import Callable

from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.species import Species
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.services.garden.nursery.list_bonsai import _build_species_map, _build_bonsai_dict


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
