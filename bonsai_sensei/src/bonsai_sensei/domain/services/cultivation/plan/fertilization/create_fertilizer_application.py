from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.cultivation.plan.planned_work_creation import execute_planned_work_creation
from bonsai_sensei.domain.services.cultivation.plan.planned_work_payload_builders import build_fertilizer_payload
from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_create_fertilizer_application_tool(
    get_bonsai_by_name_func: Callable,
    get_fertilizer_by_name_func: Callable,
    list_fertilizers_func: Callable,
    create_planned_work_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_confirmation_message: Callable,
    build_selection_question: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def create_fertilizer_application(
        bonsai_name: str,
        scheduled_date: str = "",
        fertilizer_name: str = "",
        amount: str = "",
        notes: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Plan a single fertilizer application for a bonsai on a specific date. If no fertilizer is specified, automatically selects the most suitable one from the available catalog based on the bonsai's history and needs.

        Use this when the user wants to schedule one fertilization event (not a recurring plan for a period of months).

        Args:
            bonsai_name: Name of the bonsai to plan the fertilizer application for.
            scheduled_date: Date of the planned work in ISO format (YYYY-MM-DD). Defaults to next Saturday if not provided.
            fertilizer_name: Name of the fertilizer to apply. Leave empty to auto-select from the catalog.
            amount: Amount of fertilizer to apply (e.g. "5 ml", "10 g").
            notes: Optional notes about the planned work.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_name_required", "scheduled_date_required", "no_fertilizers_available",
                "invalid_scheduled_date_format", "bonsai_not_found", "fertilizer_not_found".
        """
        if not bonsai_name:
            return {"status": "error", "message": "bonsai_name_required"}

        if not scheduled_date:
            scheduled_date = tool_context.state.get("next_saturday") if tool_context else None
        if not scheduled_date:
            return {"status": "error", "message": "scheduled_date_required"}

        user_id = resolve_confirmation_user_id(tool_context)
        if not fertilizer_name:
            fertilizers = list_fertilizers_func(user_id=user_id)
            if not fertilizers:
                return {"status": "error", "message": "no_fertilizers_available"}
            if len(fertilizers) == 1:
                fertilizer_name = fertilizers[0].name
            else:
                question = build_selection_question(bonsai_name)
                options = [fertilizer.name for fertilizer in fertilizers]
                selected = await ask_selection(question=question, options=options, tool_context=tool_context)
                if isinstance(selected, SelectionNoneResult):
                    return {"status": "cancelled", "message": "fertilizer_selection_cancelled"}
                fertilizer_name = selected

        fertilizer = get_fertilizer_by_name_func(fertilizer_name)
        if not fertilizer:
            return {"status": "error", "message": "fertilizer_not_found"}

        payload = build_fertilizer_payload(fertilizer.id, fertilizer.name, amount)
        confirmation_message = build_confirmation_message(bonsai_name, fertilizer_name, amount, scheduled_date)

        return await execute_planned_work_creation(
            bonsai_name=bonsai_name,
            work_type="fertilizer_application",
            scheduled_date=scheduled_date,
            payload=payload,
            notes=notes,
            confirmation_message=confirmation_message,
            get_bonsai_by_name_func=get_bonsai_by_name_func,
            create_planned_work_func=create_planned_work_func,
            ask_confirmation=ask_confirmation,
            tool_context=tool_context,
        )

    return create_fertilizer_application
