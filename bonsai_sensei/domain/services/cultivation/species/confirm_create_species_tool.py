from functools import partial
import uuid
from google.adk.tools.tool_context import ToolContext
from typing import Callable
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.species import Species


def create_confirm_create_species_tool(
    create_species_func,
    get_species_by_name_func: Callable[[str], Species | None],
    scientific_name_resolver: Callable[[str], dict],
    care_guide_builder: Callable[[str, str], dict],
    confirmation_store: ConfirmationStore,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="botanist")
    def confirm_create_bonsai_species(
        common_name: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Create a confirmation to register a new bonsai species with its scientific name and care guide.

        Resolves the scientific name and builds the care guide automatically using external sources.

        Args:
            common_name: Common name of the species to register.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "species_name_required",
            "species_already_exists", "scientific_name_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not common_name:
            return {"status": "error", "message": "species_name_required"}

        if get_species_by_name_func(common_name):
            return {"status": "error", "message": "species_already_exists"}

        resolution = scientific_name_resolver(common_name)
        scientific_names = resolution.get("scientific_names", [])
        if not scientific_names:
            return {"status": "error", "message": "scientific_name_not_found"}

        scientific_name = scientific_names[0]
        care_guide = care_guide_builder(common_name, scientific_name)

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                create_species_func,
                Species(
                    name=common_name,
                    scientific_name=scientific_name,
                    care_guide=care_guide,
                ),
            ),
            deduplication_key=f"create_species:{common_name}",
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Continue with the remaining steps of the plan. Do not call this tool again for the same operation.",
            "summary": summary,
        }

    return confirm_create_bonsai_species
