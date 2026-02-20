from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_update_bonsai_tool(
    update_bonsai_func,
    get_species_by_name_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="gardener")
    def confirm_update_bonsai(
        bonsai_id: int,
        summary: str,
        name: str | None = None,
        species_name: str | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to update a bonsai and return JSON with the planned changes.

        Args:
            bonsai_id: Identifier of the bonsai to update.
            summary: Short human-readable summary to show in the confirmation prompt.
            name: Optional new name for the bonsai.
            species_name: Optional common name of the new species to assign.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"confirmation": <summary>}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "bonsai_id_required",
            "species_not_found", "bonsai_update_required".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not bonsai_id:
            return {"status": "error", "message": "bonsai_id_required"}

        bonsai_data = {}
        if name is not None:
            bonsai_data["name"] = name

        if species_name is not None:
            species = get_species_by_name_func(species_name)
            if not species:
                return {"status": "error", "message": "species_not_found"}
            bonsai_data["species_id"] = species.id

        if not bonsai_data:
            return {"status": "error", "message": "bonsai_update_required"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                update_bonsai_func,
                bonsai_id=bonsai_id,
                bonsai_data=bonsai_data,
            ),
        )

        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_update_bonsai
