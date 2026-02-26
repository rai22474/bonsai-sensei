from datetime import date
from functools import partial
import uuid

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.planned_work import PlannedWork
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_confirm_create_planned_work_tool(
    get_bonsai_by_name_func,
    get_fertilizer_by_name_func,
    get_phytosanitary_by_name_func,
    create_planned_work_func,
    confirmation_store: ConfirmationStore,
):

    @limit_tool_calls(agent_name="cultivation_agent")
    def confirm_create_planned_work(
        bonsai_name: str,
        work_type: str,
        scheduled_date: str,
        summary: str,
        fertilizer_name: str = "",
        amount: str = "",
        phytosanitary_name: str = "",
        pot_size: str = "",
        pot_type: str = "",
        substrate: str = "",
        notes: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Register a confirmation to create a planned work for a bonsai.

        Args:
            bonsai_name: Name of the bonsai to plan work for.
            work_type: Type of work to plan. Valid values: "fertilizer_application",
                "transplant", "phytosanitary_application".
            scheduled_date: Date of the planned work in ISO format (YYYY-MM-DD).
            summary: Short human-readable summary to show in the confirmation prompt.
            fertilizer_name: Name of the fertilizer (required for fertilizer_application).
            amount: Amount to apply (for fertilizer_application and phytosanitary_application).
            phytosanitary_name: Name of the product (required for phytosanitary_application).
            pot_size: Size of the pot (for transplant).
            pot_type: Type/material of the pot (for transplant).
            substrate: Substrate to use (for transplant).
            notes: Optional notes about the planned work.

        Returns:
            A JSON-ready dictionary indicating whether the confirmation was registered.

        Output JSON (success): {"status": "confirmation_pending", "reason": "<instruction>", "summary": "<summary>"}.
        Output JSON (error): {"status": "error", "message": "<reason>"}.
        Error reasons: "user_id_required_for_confirmation", "bonsai_name_required",
            "work_type_required", "scheduled_date_required", "invalid_scheduled_date_format",
            "bonsai_not_found", "fertilizer_name_required", "fertilizer_not_found",
            "phytosanitary_name_required", "phytosanitary_not_found".
        """
        user_id = resolve_confirmation_user_id(tool_context)
        if not user_id:
            return {"status": "error", "message": "user_id_required_for_confirmation"}

        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not work_type:
            return {"status": "error", "message": "work_type_required"}

        if not scheduled_date:
            return {"status": "error", "message": "scheduled_date_required"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        try:
            scheduled_date_parsed = date.fromisoformat(scheduled_date)
        except ValueError:
            return {"status": "error", "message": "invalid_scheduled_date_format"}

        if work_type == "fertilizer_application":
            if not fertilizer_name:
                return {"status": "error", "message": "fertilizer_name_required"}
            fertilizer = get_fertilizer_by_name_func(fertilizer_name)
            if not fertilizer:
                return {"status": "error", "message": "fertilizer_not_found"}
            payload = {
                "fertilizer_id": fertilizer.id,
                "fertilizer_name": fertilizer_name,
                "amount": amount,
            }
        elif work_type == "phytosanitary_application":
            if not phytosanitary_name:
                return {"status": "error", "message": "phytosanitary_name_required"}
            phytosanitary = get_phytosanitary_by_name_func(phytosanitary_name)
            if not phytosanitary:
                return {"status": "error", "message": "phytosanitary_not_found"}
            payload = {
                "phytosanitary_id": phytosanitary.id,
                "phytosanitary_name": phytosanitary_name,
                "amount": amount,
            }
        else:
            payload = {
                key: value
                for key, value in {
                    "pot_size": pot_size,
                    "pot_type": pot_type,
                    "substrate": substrate,
                }.items()
                if value
            }

        command = Confirmation(
            id=uuid.uuid4().hex,
            user_id=user_id,
            summary=summary,
            executor=partial(
                create_planned_work_func,
                planned_work=PlannedWork(
                    bonsai_id=bonsai.id,
                    work_type=work_type,
                    payload=payload,
                    scheduled_date=scheduled_date_parsed,
                    notes=notes if notes else None,
                ),
            ),
            deduplication_key=f"create_planned_work:{bonsai_name}:{work_type}:{scheduled_date}",
        )

        confirmation_store.set_pending(user_id, command)
        return {
            "status": "confirmation_pending",
            "reason": "The operation has been queued and is awaiting user confirmation. Do not call this tool again — inform the user of the pending confirmation and wait for their approval.",
            "summary": summary,
        }

    return confirm_create_planned_work
