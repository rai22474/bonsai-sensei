from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_confirm_delete_planned_work_tool(
    get_planned_work_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
):
    @trace_tool_call
    @limit_tool_calls(agent_name="planning_agent")
    async def confirm_delete_planned_work(
        planned_work_id: int,
        summary: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Delete a planned work after explicit user confirmation.

        Args:
            planned_work_id: ID of the planned work to delete.
            summary: Short human-readable summary to show in the confirmation prompt.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "message": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "planned_work_not_found".
        """
        work = get_planned_work_func(work_id=planned_work_id)
        if not work:
            return {"status": "error", "message": "planned_work_not_found"}

        confirmation_prompt = _build_delete_confirmation(work)
        confirmed = await ask_confirmation(confirmation_prompt, tool_context=tool_context)

        if confirmed:
            delete_planned_work_func(work_id=planned_work_id)
            return {"status": "success", "message": f"Planned work {planned_work_id} deleted."}

        return {"status": "cancelled", "message": "Operation cancelled by user."}

    return confirm_delete_planned_work


def _build_delete_confirmation(work) -> str:
    from datetime import date, datetime
    scheduled = work.scheduled_date
    if isinstance(scheduled, str):
        scheduled = datetime.strptime(scheduled, "%Y-%m-%d").date()
    date_str = scheduled.strftime("%d/%m/%Y")
    work_type = work.work_type
    payload = work.payload or {}

    if work_type == "fertilizer_application":
        fertilizer_name = payload.get("fertilizer_name", "fertilizante desconocido")
        amount = payload.get("amount")
        detail = f"'{fertilizer_name}'" + (f" ({amount})" if amount else "")
        return f"¿Eliminar aplicación de fertilizante {detail} del {date_str}?"

    if work_type == "phytosanitary_application":
        product_name = payload.get("phytosanitary_name", "producto desconocido")
        amount = payload.get("amount")
        detail = f"'{product_name}'" + (f" ({amount})" if amount else "")
        return f"¿Eliminar aplicación fitosanitaria {detail} del {date_str}?"

    if work_type == "transplant":
        parts = [value for key in ("pot_size", "pot_type", "substrate") if (value := payload.get(key))]
        detail = f" ({', '.join(parts)})" if parts else ""
        return f"¿Eliminar trasplante{detail} del {date_str}?"

    return f"¿Eliminar trabajo '{work_type}' del {date_str}?"
