from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_update_species_tool(
    update_species_func,
    get_species_by_name_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="botanist")
    def confirm_update_species(
        species: dict,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to update a species and return JSON with the planned changes.

        Args:
            species: A mapping with fields to update. Use 'name' or 'common_name' to
                identify the species to update. Use 'common_name' to rename it and
                'scientific_name' to update its scientific name.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"confirmation": <summary>}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "species_name_required",
            "species_update_required", "species_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", 
                    "message": "user_id_required_for_confirmation"}

        species_name = species.get("name") or species.get("common_name")
        if not species_name:
            return {"status": "error", 
                    "message": "species_name_required"}

        common_name = species.get("common_name")
        scientific_name = species.get("scientific_name")

        species_data = {}
        if common_name is not None:
            species_data["name"] = common_name
        if scientific_name is not None:
            species_data["scientific_name"] = scientific_name

        if not species_data:
            return {"status": "error", 
                    "message": "species_update_required"}

        existing_species = get_species_by_name_func(species_name)
        if not existing_species:
            return {"status": "error", 
                    "message": "species_not_found"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                update_species_func,
                species_id=existing_species.id,
                species_data=species_data,
            ),
        )
        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_update_species
