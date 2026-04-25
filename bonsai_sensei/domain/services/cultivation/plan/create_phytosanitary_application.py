from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.cultivation.plan.planned_work_creation import execute_planned_work_creation
from bonsai_sensei.domain.services.cultivation.plan.planned_work_payload_builders import build_phytosanitary_payload
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_phytosanitary_application_tool(
    get_bonsai_by_name_func: Callable,
    get_phytosanitary_by_name_func: Callable,
    create_planned_work_func: Callable,
    ask_confirmation: Callable,
    build_confirmation_message: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="planning_agent")
    async def create_phytosanitary_application(
        bonsai_name: str,
        scheduled_date: str,
        phytosanitary_name: str,
        amount: str = "",
        notes: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Plan a phytosanitary treatment for a bonsai after explicit user confirmation.

        Args:
            bonsai_name: Name of the bonsai to plan the phytosanitary treatment for.
            scheduled_date: Date of the planned work in ISO format (YYYY-MM-DD).
            phytosanitary_name: Name of the phytosanitary product to apply.
            amount: Amount of product to apply (e.g. "2 ml", "5 g").
            notes: Optional notes about the planned work.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "scheduled_date_required", "phytosanitary_name_required",
                "invalid_scheduled_date_format", "bonsai_not_found", "phytosanitary_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not scheduled_date:
            scheduled_date = tool_context.state.get("next_saturday") if tool_context else None
        if not scheduled_date:
            return {"status": "error", "message": "scheduled_date_required"}

        if not phytosanitary_name:
            return {"status": "error", "message": "phytosanitary_name_required"}

        phytosanitary = get_phytosanitary_by_name_func(phytosanitary_name)
        if not phytosanitary:
            return {"status": "error", "message": "phytosanitary_not_found"}

        payload = build_phytosanitary_payload(phytosanitary.id, phytosanitary_name, amount)
        confirmation_message = build_confirmation_message(bonsai_name, phytosanitary_name, amount, scheduled_date)

        return await execute_planned_work_creation(
            bonsai_name=bonsai_name,
            work_type="phytosanitary_application",
            scheduled_date=scheduled_date,
            payload=payload,
            notes=notes,
            confirmation_message=confirmation_message,
            get_bonsai_by_name_func=get_bonsai_by_name_func,
            create_planned_work_func=create_planned_work_func,
            ask_confirmation=ask_confirmation,
            tool_context=tool_context,
        )

    return create_phytosanitary_application
