from datetime import date
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.services.cultivation.plan.refinement.start_work_documentation import (
    _STATE_PHOTO_ANALYSES,
)
from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_TEMPLATE_ENV = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))


def create_analyze_work_photo_tool(
    run_photo_analysis_func: Callable,
    get_pending_photo_bytes: Callable,
    save_session_photo: Callable,
    clear_pending_photo: Callable,
    get_bonsai_by_id_func: Callable,
    get_planned_work_func: Callable,
) -> Callable:
    @trace_tool_call
    async def analyze_work_photo(
        work_id: int | None = None,
        session_type: str = "analysis",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Analyze the photo sent by the user in the context of the current work session.

        Call this immediately when the user sends a photo during a kiroku session.
        The analysis is contextual — it considers the specific work type and objective.
        The photo is stored in a session-specific folder (not in the general gallery).

        Args:
            work_id: ID of the planned work being documented (from session context).
            session_type: "analysis" for pre-work, "result" for post-work documentation.
            tool_context: ADK tool context.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        photo_bytes = get_pending_photo_bytes(user_id)
        if not photo_bytes:
            return {"status": "error", "message": "no_pending_photo"}

        analyses = list(tool_context.state.get(_STATE_PHOTO_ANALYSES, []))
        photo_count = len(analyses) + 1

        work = get_planned_work_func(work_id=work_id) if work_id else None
        bonsai = get_bonsai_by_id_func(bonsai_id=work.bonsai_id) if work else None
        work_type = work.work_type if work else ""
        bonsai_name = bonsai.name if bonsai else ""
        session_user_id = bonsai.user_id if bonsai and bonsai.user_id else user_id
        session_date = date.today().isoformat()

        save_session_photo(session_user_id, work_id, session_date, photo_count, photo_bytes)

        template = _TEMPLATE_ENV.get_template("work_photo_analysis.j2")
        instruction = template.render(
            bonsai_name=bonsai_name,
            work_type=work_type,
            session_type=session_type,
        )

        analysis = await run_photo_analysis_func(photo_bytes, instruction)

        analyses.append(f"Foto {photo_count}: {analysis}")
        tool_context.state[_STATE_PHOTO_ANALYSES] = analyses

        clear_pending_photo(user_id)
        return {"status": "success", "analysis": analysis, "photo_number": photo_count}

    return analyze_work_photo
