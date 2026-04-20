from datetime import date
from typing import Callable

from bonsai_sensei.domain.planned_work import PlannedWork


async def execute_planned_work_creation(
    bonsai_name: str,
    work_type: str,
    scheduled_date: str,
    payload: dict,
    notes: str,
    confirmation_message: str,
    get_bonsai_by_name_func: Callable,
    create_planned_work_func: Callable,
    ask_confirmation: Callable,
    tool_context,
) -> dict:
    bonsai = get_bonsai_by_name_func(bonsai_name)
    if not bonsai:
        return {"status": "error", "message": "bonsai_not_found"}

    try:
        scheduled_date_parsed = date.fromisoformat(scheduled_date)
    except ValueError:
        return {"status": "error", "message": "invalid_scheduled_date_format"}

    confirmed = await ask_confirmation(confirmation_message, tool_context=tool_context)
    if not confirmed:
        return {"status": "cancelled", "message": "Operation cancelled by user."}

    create_planned_work_func(
        planned_work=PlannedWork(
            bonsai_id=bonsai.id,
            work_type=work_type,
            payload=payload,
            scheduled_date=scheduled_date_parsed,
            notes=notes if notes else None,
        )
    )
    return {"status": "success", "message": f"Planned work for '{bonsai_name}' created."}
