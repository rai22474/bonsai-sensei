from functools import partial
import uuid
from bonsai_sensei.domain.bonsai import Bonsai
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_create_bonsai_tool(
    create_bonsai_func,
    find_species_by_id_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="gardener")
    def confirm_create_bonsai(
        name: str,
        species_id: int,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """A confirmation request to the users to confirm to create a bonsai and return JSON with status and created record.

        Args:
            name: Bonsai name.
            species_id: Species identifier.

        Returns:
            A JSON-ready dictionary with the confirmation creation result.

        Output JSON (success): {"confirmation": <summary>}.
        Output JSON (error): {"status":"error","message":"..."}.
        """
        if not name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not species_id:
            return {"status": "error", "message": "species_id_required"}

        species = find_species_by_id_func(species_id)

        if not species:
            return {"status": "error", "message": "species_not_found"}

        user_id = resolve_confirmation_user_id(tool_context)

        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                create_bonsai_func, bonsai=Bonsai(name=name, species_id=species_id)
            ),
        )

        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_create_bonsai
