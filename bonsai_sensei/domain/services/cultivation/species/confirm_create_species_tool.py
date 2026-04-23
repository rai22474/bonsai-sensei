from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.species import Species


def create_confirm_create_species_tool(
    create_species_func: Callable,
    get_species_by_name_func: Callable[[str], Species | None],
    scientific_name_resolver: Callable[[str], dict],
    wiki_page_builder: Callable[[str, str], str],
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    async def confirm_create_bonsai_species(
        common_name: str,
        scientific_name: str | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a new bonsai species. Looks up its scientific name and generates its cultivation guide.

        When scientific_name is not provided, the tool searches external botanical sources to find it.
        If a single match is found, it proceeds. If multiple candidates exist, returns 'ambiguous' so
        the agent can present the options and let the user choose — then call this tool again with
        the chosen scientific_name.

        Once the scientific name is confirmed by the user, the tool generates a full cultivation guide
        (wiki page) and persists the species.

        Args:
            common_name: Common name of the species to register.
            scientific_name: Optional. Provide when the user has already chosen from an ambiguous result.
                If omitted, the tool resolves it from external botanical sources.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "species_name_required", "species_already_exists", "scientific_name_not_found".
        """
        if not common_name:
            return {"status": "error", "message": "species_name_required"}

        if get_species_by_name_func(common_name):
            return {"status": "error", "message": "species_already_exists"}

        if not scientific_name:
            resolution = scientific_name_resolver(common_name)
            scientific_names = resolution.get("scientific_names", [])
            if not scientific_names:
                return {"status": "error", "message": "scientific_name_not_found"}
            if len(scientific_names) > 1:
                scientific_name = await ask_selection(
                    f"Se encontraron varios nombres científicos para '{common_name}'. ¿Cuál es el correcto?",
                    scientific_names,
                    tool_context=tool_context,
                )
            else:
                scientific_name = scientific_names[0]

        confirmed = await ask_confirmation(
            build_confirmation_message(common_name, scientific_name),
            tool_context=tool_context,
        )

        if confirmed:
            wiki_path = await wiki_page_builder(common_name, scientific_name)
            create_species_func(
                Species(
                    name=common_name,
                    scientific_name=scientific_name,
                    wiki_path=wiki_path,
                )
            )
            return {"status": "success", "message": f"Species '{common_name}' created."}

        return {"status": "cancelled", "reason": confirmed.reason}

    return confirm_create_bonsai_species
