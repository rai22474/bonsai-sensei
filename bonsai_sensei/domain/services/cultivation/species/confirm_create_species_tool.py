from functools import partial
import uuid
from google.adk.tools.tool_context import ToolContext
from typing import Optional
from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.resolve_user_id import (
    resolve_confirmation_user_id,
)
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.species import Species


def create_confirm_create_species_tool(
    create_species_func,
    confirmation_store: ConfirmationStore,
):
    @limit_tool_calls(agent_name="botanist")
    def confirm_create_bonsai_species(
        common_name: str,
        scientific_name: str,
        summary: str,
        sources: list[str],
        watering: str | None = None,
        light: str | None = None,
        soil: str | None = None,
        pruning: str | None = None,
        pests: str | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Create a confirmation to create a species and return JSON with care guide details.

        Args:
            common_name: Common name for the species.
            scientific_name: Scientific name to register.
            summary: Summary of the care guide.
            sources: Source URLs for the care guide.
            watering: Watering guidance.
            light: Light requirements.
            soil: Soil requirements.
            pruning: Pruning guidance.
            pests: Pest or disease guidance.

        Returns:
            A JSON-ready dictionary with creation results.

        Output JSON (success): {"confirmation": True, "summary": <summary>}.
        Output JSON (error): {"status":"error","message":"..."}.
        """

        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        normalized_scientific = _normalize_scientific_name(scientific_name)

        if not normalized_scientific:
            return {
                "common_name": common_name,
                "scientific_name": None,
                "candidates": [],
                "needs_scientific_name": True,
            }

        care_guide_payload = {
            "summary": summary,
            "sources": sources,
            "watering": watering,
            "light": light,
            "soil": soil,
            "pruning": pruning,
            "pests": pests,
        }

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                create_species_func,
                Species(
                    name=common_name,
                    scientific_name=normalized_scientific,
                    care_guide=care_guide_payload,
                ),
            ),
        )

        confirmation_store.set_pending(user_id, command)

        return {"confirmation": summary}

    return confirm_create_bonsai_species


def _normalize_scientific_name(scientific_name: Optional[str]) -> Optional[str]:
    """Trim and validate a scientific name string.

    Returns the trimmed name or None when the input is None or consists only of
    whitespace. This centralizes the normalization rule used before creating
    species records.
    """

    if scientific_name is None:
        return None

    trimmed = scientific_name.strip()
    return trimmed if trimmed else None
