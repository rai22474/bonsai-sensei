from google.adk.tools.tool_context import ToolContext
from functools import partial
from typing import Callable
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.domain.services.storekeeper.fertilizers.fertilizer_tools import _extract_recommended_amount


def create_confirm_create_fertilizer_tool(
    create_fertilizer_func,
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
    searcher: Callable[[str], dict],
    confirmation_store: ConfirmationStore,
):

    @trace_tool_call
    @limit_tool_calls(agent_name="storekeeper")
    def confirm_create_fertilizer(
        name: str,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Search for the fertilizer guide online and register a confirmation to create it.

        Args:
            name: Fertilizer name.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "fertilizer_name_required", "fertilizer_already_exists".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}

        if get_fertilizer_by_name_func(name):
            return {"status": "error", "message": "fertilizer_already_exists"}

        search_response = searcher(f"{name} bonsai dosis de uso ficha tecnica fertilizante")
        answer = str(search_response.get("answer", "")).strip()
        sources = [str(item.get("url")) for item in search_response.get("results", []) if item.get("url")]
        usage_sheet = answer or "No data available."
        recommended_amount = _extract_recommended_amount(answer)

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                create_fertilizer_func,
                fertilizer=Fertilizer(
                    name=name,
                    usage_sheet=usage_sheet,
                    recommended_amount=recommended_amount,
                    sources=sources,
                ),
            ),
            deduplication_key=f"create_fertilizer:{name}",
        )
        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_create_fertilizer
