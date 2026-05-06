from typing import Callable

from bonsai_sensei.domain.bonsai import Bonsai
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.garden.bonsai_index_page import build_bonsai_index_page, build_bonsai_wiki_path
from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_bonsai_tool(
    create_bonsai_func: Callable,
    list_species_func: Callable,
    get_species_by_name_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_selection_question: Callable,
    build_confirmation_message: Callable,
    write_wiki_page_func: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="gardener")
    async def create_bonsai(
        name: str,
        species_name: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Create a new bonsai in the collection after explicit user confirmation.

        Args:
            name: Bonsai name.
            species_name: Common name of the species to assign to the bonsai. If empty, user selects from a list.

        Returns:
            A JSON-ready dictionary with status 'success' or 'cancelled'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "no_species_available", "species_not_found".
        """
        if not name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not species_name:
            all_species = list_species_func()
            if not all_species:
                return {"status": "error", "message": "no_species_available"}
            species_names = [species.name for species in all_species]
            selection = await ask_selection(
                build_selection_question(),
                species_names,
                tool_context=tool_context,
            )
            if isinstance(selection, SelectionNoneResult):
                return {"status": "cancelled", "reason": selection.reason}
            species_name = selection

        species = get_species_by_name_func(species_name)
        if not species:
            return {"status": "error", "message": "species_not_found"}

        confirmed = await ask_confirmation(build_confirmation_message(name, species_name), tool_context=tool_context)

        if confirmed:
            wiki_path = build_bonsai_wiki_path(name)
            index_content = build_bonsai_index_page(name, species.name, species.wiki_path)
            write_wiki_page_func(path=wiki_path, content=index_content)
            create_bonsai_func(bonsai=Bonsai(name=name, species_id=species.id, wiki_path=wiki_path))
            return {"status": "success", "message": f"Bonsai '{name}' created.", "species_name": species.name}

        return {"status": "cancelled", "reason": confirmed.reason}

    return create_bonsai
