from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_delete_species_tool(
    delete_species_func,
    get_species_by_name_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="botanist")
    def confirm_delete_species(
        species_name: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to delete a species and return JSON with the result.

        Args:
            species_name: The common name of the species to delete.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"confirmation": <summary>}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "species_name_required",
            "species_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", 
                    "message": "user_id_required_for_confirmation"}

        if not species_name:
            return {"status": "error", 
                    "message": "species_name_required"}

        existing_species = get_species_by_name_func(species_name)
        if not existing_species:
            return {"status": "error", 
                    "message": "species_not_found"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                delete_species_func,
                species_id=existing_species.id,
            ),
        )

        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_delete_species
