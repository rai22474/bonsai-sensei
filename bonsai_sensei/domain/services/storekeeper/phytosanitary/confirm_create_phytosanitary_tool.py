from google.adk.tools.tool_context import ToolContext
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_create_phytosanitary_tool(
    create_phytosanitary_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def confirm_create_phytosanitary(
        name: str,
        target: str,
        usage_sheet: str,
        summary: str,
        sources: list[str] | None = None,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to create a phytosanitary product and return JSON with the result.

        Args:
            name: Product name.
            target: The pest/disease this product targets.
            usage_sheet: Usage instructions or technical sheet.
            summary: Short human-readable summary to show in the confirmation prompt.
            sources: Optional list of source URLs.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"confirmation": <summary>}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "phytosanitary_name_required",
            "usage_sheet_required", "recommended_for_required".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        if not usage_sheet:
            return {"status": "error", "message": "usage_sheet_required"}

        if not target:
            return {"status": "error", "message": "recommended_for_required"}

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                create_phytosanitary_func,
                phytosanitary=Phytosanitary(
                    name=name,
                    usage_sheet=usage_sheet,
                    recommended_for=target,
                    sources=sources or [],
                ),
            ),
        )
        confirmation_store.set_pending(user_id, command)
        return {"confirmation": summary}

    return confirm_create_phytosanitary
