from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.human_input import SelectionNoneResult, resolve_bonsai_name
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

SESSION_TYPE_ANALYSIS = "analysis"
SESSION_TYPE_RESULT = "result"

_STATE_WORK_ID = "kiroku_work_id"
_STATE_WORK_TYPE = "kiroku_work_type"
_STATE_BONSAI_NAME = "kiroku_bonsai_name"
_STATE_SESSION_TYPE = "kiroku_session_type"
_STATE_PHOTO_ANALYSES = "kiroku_photo_analyses"

_STATE_ACTIVE_CHANNEL = "active_channel"
KIROKU_CHANNEL = "kiroku"

ALL_STATE_KEYS = [
    _STATE_WORK_ID, _STATE_WORK_TYPE, _STATE_BONSAI_NAME,
    _STATE_SESSION_TYPE, _STATE_PHOTO_ANALYSES,
]


def create_start_work_documentation_tool(
    get_bonsai_by_name_func: Callable,
    list_planned_works_func: Callable,
    ask_human: Callable,
    ask_selection: Callable,
    build_bonsai_name_question: Callable,
    build_work_selection_question: Callable,
    build_work_option_label: Callable,
) -> Callable:
    @trace_tool_call
    async def start_work_documentation(
        bonsai_name: str | None = None,
        session_type: str = SESSION_TYPE_ANALYSIS,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Start a work documentation session for a bonsai's planned work.

        Lists the bonsai's planned works and lets the user pick one.
        Stores session context (work, bonsai, mode) for subsequent tools.

        Use session_type="analysis" for pre-work planning, "result" for
        documenting a completed work.

        Args:
            bonsai_name: Name of the bonsai. Asks if not provided.
            session_type: "analysis" (pre-work) or "result" (post-work).
            tool_context: ADK tool context.
        """
        bonsai_name = await resolve_bonsai_name(bonsai_name, ask_human, build_bonsai_name_question, tool_context)
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        works = list_planned_works_func(bonsai_id=bonsai.id)
        if not works:
            return {"status": "error", "message": "no_planned_works"}

        if len(works) > 1:
            options = [build_work_option_label(work) for work in works]
            selection = await ask_selection(
                build_work_selection_question(bonsai_name),
                options,
                tool_context=tool_context,
            )
            if isinstance(selection, SelectionNoneResult):
                return {"status": "cancelled", "reason": selection.reason}
            selected_index = options.index(selection) if selection in options else 0
            work = works[selected_index]
        else:
            work = works[0]

        tool_context.state[_STATE_WORK_ID] = work.id
        tool_context.state[_STATE_WORK_TYPE] = work.work_type
        tool_context.state[_STATE_BONSAI_NAME] = bonsai_name
        tool_context.state[_STATE_SESSION_TYPE] = session_type
        tool_context.state[_STATE_PHOTO_ANALYSES] = []
        tool_context.state[_STATE_ACTIVE_CHANNEL] = KIROKU_CHANNEL

        return {
            "status": "success",
            "work_id": work.id,
            "work_type": work.work_type,
            "scheduled_date": work.scheduled_date.isoformat(),
            "session_type": session_type,
            "notes": work.notes,
        }

    return start_work_documentation
