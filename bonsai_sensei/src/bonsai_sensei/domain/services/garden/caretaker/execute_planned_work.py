from typing import Callable

from bonsai_sensei.domain.bonsai_event import BonsaiEvent
from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.human_input import SelectionNoneResult
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


async def execute_planned_work(
    bonsai_name: str,
    get_bonsai_by_name_func: Callable,
    list_planned_works_func: Callable,
    record_bonsai_event_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_confirmation_message: Callable,
    build_selection_question: Callable,
    build_work_option_label: Callable,
    user_id: str | None = None,
    tool_context=None,
) -> dict:
    """Core planned work execution logic shared by the ADK tool and direct Telegram commands."""
    bonsai = get_bonsai_by_name_func(bonsai_name)
    if not bonsai:
        return {"status": "error", "message": "bonsai_not_found"}

    works = list_planned_works_func(bonsai_id=bonsai.id)
    if not works:
        return {"status": "error", "message": "no_planned_works"}

    if len(works) > 1:
        options = [build_work_option_label(work) for work in works]
        selection = await ask_selection(
            build_selection_question(bonsai_name),
            options,
            user_id=user_id,
            tool_context=tool_context,
        )
        if isinstance(selection, SelectionNoneResult):
            return {"status": "cancelled", "reason": selection.reason}
        selected_index = options.index(selection) if selection in options else -1
        if selected_index == -1:
            return {"status": "error", "message": "invalid_selection"}
        work = works[selected_index]
    else:
        work = works[0]

    confirmed = await ask_confirmation(
        build_confirmation_message(work, bonsai_name),
        user_id=user_id,
        tool_context=tool_context,
    )
    if not confirmed:
        return {"status": "cancelled", "reason": confirmed.reason}

    record_bonsai_event_func(
        bonsai_event=BonsaiEvent(
            bonsai_id=work.bonsai_id,
            event_type=work.work_type,
            payload=work.payload,
        )
    )
    delete_planned_work_func(work_id=work.id)
    return {"status": "success", "message": f"Work '{work.work_type}' executed for '{bonsai_name}'."}


def create_execute_planned_work_tool(
    get_bonsai_by_name_func: Callable,
    list_planned_works_func: Callable,
    record_bonsai_event_func: Callable,
    delete_planned_work_func: Callable,
    ask_confirmation: Callable,
    ask_selection: Callable,
    build_confirmation_message: Callable,
    build_selection_question: Callable,
    build_work_option_label: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="caretaker")
    async def execute_planned_work_for_bonsai(
        bonsai_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Execute a planned work for a bonsai after user confirmation. Handles work selection internally if multiple works are scheduled.

        Call this directly with just the bonsai name — do not list planned works beforehand.
        This tool handles work listing, selection (if multiple), and confirmation internally.

        Args:
            bonsai_name: Name of the bonsai whose planned work to execute.

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "message": "<confirmation>"}.
            Output JSON (cancelled): {"status": "cancelled", "reason": "<reason>"}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
            Error reasons: "bonsai_not_found", "no_planned_works".
        """
        return await execute_planned_work(
            bonsai_name=bonsai_name,
            get_bonsai_by_name_func=get_bonsai_by_name_func,
            list_planned_works_func=list_planned_works_func,
            record_bonsai_event_func=record_bonsai_event_func,
            delete_planned_work_func=delete_planned_work_func,
            ask_confirmation=ask_confirmation,
            ask_selection=ask_selection,
            build_confirmation_message=build_confirmation_message,
            build_selection_question=build_selection_question,
            build_work_option_label=build_work_option_label,
            tool_context=tool_context,
        )

    return execute_planned_work_for_bonsai
