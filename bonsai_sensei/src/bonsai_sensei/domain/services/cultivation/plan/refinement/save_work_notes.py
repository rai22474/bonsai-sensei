from datetime import date
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from google.genai import types
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.services.cultivation.plan.plan_context import bonsai_slug
from bonsai_sensei.domain.services.cultivation.plan.wiki_utils import read_wiki_content
from bonsai_sensei.domain.services.cultivation.plan.refinement.start_work_documentation import (
    ALL_STATE_KEYS,
    SESSION_TYPE_RESULT,
    _STATE_ACTIVE_CHANNEL,
    _STATE_PHOTO_ANALYSES,
)
from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_TEMPLATE_ENV = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

WIKI_INSTRUCTION = """
Eres un experto en bonsái. Redacta una página de wiki estructurada en Markdown con el análisis
y las conclusiones de una sesión de trabajo. La página debe:
- Estar en castellano
- Ser detallada y técnicamente correcta
- Servir como referencia para ejecutar o aprender del trabajo
Responde ÚNICAMENTE con el contenido Markdown, sin texto adicional.
"""


def create_document_work_session_tool(
    run_wiki_generator: Callable,
    get_planned_work_func: Callable,
    get_bonsai_by_id_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    get_development_plan_func: Callable | None = None,
    update_refinement_wiki_path_func: Callable | None = None,
    update_result_wiki_path_func: Callable | None = None,
    link_recent_photos_func: Callable | None = None,
) -> Callable:
    @trace_tool_call
    async def document_work_session(
        notes: str = "",
        work_id: int | None = None,
        session_type: str = "analysis",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Write the work session wiki page with the notes and context gathered.

        Call when ready to save the documentation. Pass the work_id and session_type
        from the session context. After this, call close_work_session with the returned wiki_path.

        Args:
            notes: Full synthesis of the session — conclusions, decisions, observations.
            work_id: ID of the planned work being documented (from session context).
            session_type: "analysis" for pre-work, "result" for post-work documentation.
            tool_context: ADK tool context.
        """
        photo_analyses = list(tool_context.state.get(_STATE_PHOTO_ANALYSES, []))

        if not work_id:
            return {"status": "error", "message": "no_active_session"}

        work = get_planned_work_func(work_id=work_id)
        if not work:
            return {"status": "error", "message": "work_not_found"}

        bonsai = get_bonsai_by_id_func(bonsai_id=work.bonsai_id)
        work_type = work.work_type
        bonsai_name = bonsai.name if bonsai else ""
        user_id = (bonsai.user_id if bonsai and bonsai.user_id else "default")

        today = date.today().isoformat()
        work_slug = work_type.lower().replace(" ", "-")
        wiki_subdir = "results" if session_type == SESSION_TYPE_RESULT else "refinements"
        template_name = "work_result_prompt.j2" if session_type == SESSION_TYPE_RESULT else "work_analysis_prompt.j2"

        wiki_path = _build_wiki_path(
            matching_works=[work],
            get_development_plan_func=get_development_plan_func,
            user_id=user_id,
            bonsai_name=bonsai_name,
            wiki_subdir=wiki_subdir,
            work_slug=work_slug,
            today=today,
        )
        plan_wiki_content = _load_plan_wiki([work], get_development_plan_func, read_wiki_page_func)
        bonsai_wiki_content = read_wiki_content(bonsai.wiki_path, read_wiki_page_func) if bonsai and bonsai.wiki_path else ""

        template = _TEMPLATE_ENV.get_template(template_name)
        rendered = template.render(
            bonsai_name=bonsai_name,
            work_type=work_type,
            notes=notes,
            photo_analyses=photo_analyses,
            bonsai_wiki_content=bonsai_wiki_content,
            plan_wiki_content=plan_wiki_content,
            planned_works=[work],
            today=today,
        )

        message = types.Content(role="user", parts=[types.Part(text=rendered)])
        wiki_content = await extract_text_from_events(run_wiki_generator(message))
        write_wiki_page_func(path=wiki_path, content=wiki_content)

        if session_type == SESSION_TYPE_RESULT:
            if update_result_wiki_path_func:
                update_result_wiki_path_func(work_id=work_id, wiki_path=wiki_path)
            if link_recent_photos_func:
                link_recent_photos_func(bonsai_id=work.bonsai_id, planned_work_id=work_id)
        else:
            if update_refinement_wiki_path_func:
                update_refinement_wiki_path_func(work_id=work_id, wiki_path=wiki_path)

        return {
            "status": "success",
            "wiki_path": wiki_path,
            "work_type": work_type,
            "bonsai_name": bonsai_name,
            "session_type": session_type,
        }

    return document_work_session


def create_close_work_session_tool() -> Callable:
    @trace_tool_call
    async def close_work_session(
        wiki_path: str = "",
        work_type: str = "",
        bonsai_name: str = "",
        session_type: str = "analysis",
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Close the kiroku documentation session after the wiki has been written.

        Call immediately after write_work_wiki succeeds, passing back the values
        returned by that tool. Clears session state and releases the channel.

        Args:
            wiki_path: Path of the wiki page just written (returned by write_work_wiki).
            work_type: Work type of the session (returned by write_work_wiki).
            bonsai_name: Bonsai name of the session (returned by write_work_wiki).
            session_type: Session type (returned by write_work_wiki).
            tool_context: ADK tool context.
        """
        session_summary = (
            f"Sesión kiroku completada — {work_type} en '{bonsai_name}'. "
            f"Tipo: {'resultado' if session_type == SESSION_TYPE_RESULT else 'análisis previo'}. "
            f"Wiki guardada en: {wiki_path}"
        )
        tool_context.state["channel_handoff_summary"] = session_summary
        tool_context.state[_STATE_ACTIVE_CHANNEL] = None
        for key in ALL_STATE_KEYS:
            tool_context.state[key] = None
        return {"status": "closed"}

    return close_work_session


def _build_wiki_path(
    matching_works: list,
    get_development_plan_func: Callable | None,
    user_id: str,
    bonsai_name: str,
    wiki_subdir: str,
    work_slug: str,
    today: str,
) -> str:
    slug = bonsai_slug(bonsai_name)
    if get_development_plan_func and matching_works:
        plan_id = next(
            (w.development_plan_id for w in matching_works if w.development_plan_id is not None),
            None,
        )
        if plan_id is not None:
            plan = get_development_plan_func(plan_id=plan_id)
            if plan:
                plan_dir = plan.wiki_path.removesuffix(".md")
                return f"{plan_dir}/{wiki_subdir}/{work_slug}-{today}.md"
    return f"users/{user_id}/bonsai/{slug}/{wiki_subdir}/{work_slug}-{today}.md"


def _load_plan_wiki(
    matching_works: list,
    get_development_plan_func: Callable | None,
    read_wiki_page_func: Callable,
) -> str:
    if not get_development_plan_func or not matching_works:
        return ""
    plan_id = next(
        (w.development_plan_id for w in matching_works if w.development_plan_id is not None),
        None,
    )
    if plan_id is None:
        return ""
    plan = get_development_plan_func(plan_id=plan_id)
    if not plan:
        return ""
    return read_wiki_content(plan.wiki_path, read_wiki_page_func)
