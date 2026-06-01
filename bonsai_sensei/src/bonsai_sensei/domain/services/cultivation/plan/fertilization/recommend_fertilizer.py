import re
from datetime import date
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_fertilizer_recommender_func(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_fertilizers_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    run_recommendation: Callable,
) -> Callable:
    """Create a callable that selects the best fertilizer for a bonsai without ADK tool decorators."""
    async def recommend(bonsai_name: str) -> dict:
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        fertilizers = list_fertilizers_func()
        if not fertilizers:
            return {"status": "error", "message": "no_fertilizers_available"}

        events = list_bonsai_events_func(bonsai.id) or []

        plan_path = _build_plan_path(bonsai_name)
        existing_plan_result = read_wiki_page_func(path=plan_path)
        existing_plan = existing_plan_result.get("content", "") if existing_plan_result.get("status") == "success" else ""

        fertilizer_pages = {}
        for fertilizer in fertilizers:
            if fertilizer.wiki_path:
                page_result = read_wiki_page_func(path=fertilizer.wiki_path)
                if page_result.get("status") == "success":
                    fertilizer_pages[fertilizer.name] = page_result["content"]

        context = _build_context(bonsai_name, date.today().isoformat(), events, existing_plan, fertilizers, fertilizer_pages)
        recommendation = await run_recommendation(context)

        write_wiki_page_func(path=plan_path, content=recommendation["wiki_content"])

        return {
            "status": "success",
            "fertilizer_name": recommendation["fertilizer_name"],
            "reasoning": recommendation["reasoning"],
        }

    return recommend


def create_recommend_fertilizer_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_fertilizers_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    run_recommendation: Callable,
) -> Callable:
    recommend = create_fertilizer_recommender_func(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_bonsai_events_func=list_bonsai_events_func,
        list_fertilizers_func=list_fertilizers_func,
        read_wiki_page_func=read_wiki_page_func,
        write_wiki_page_func=write_wiki_page_func,
        run_recommendation=run_recommendation,
    )

    @trace_tool_call
    async def recommend_fertilizer(
        bonsai_name: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Recommend the best fertilizer for a bonsai based on its history, existing plan, and available fertilizers. Saves the recommendation and rationale in the bonsai's wiki.

        Args:
            bonsai_name: Name of the bonsai to recommend fertilizer for.

        Returns:
            A JSON-ready dictionary with status 'success' and the recommendation, or 'error'.
            Output JSON (success): {"status": "success", "fertilizer_name": "...", "reasoning": "..."}.
            Output JSON (error): {"status": "error", "message": "bonsai_not_found" | "no_fertilizers_available"}.
        """
        return await recommend(bonsai_name)

    return recommend_fertilizer


def _build_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _build_plan_path(bonsai_name: str) -> str:
    return f"bonsai/{_build_slug(bonsai_name)}/fertilization-plan.md"


def _build_context(bonsai_name: str, current_date: str, events: list, existing_plan: str, fertilizers: list, fertilizer_pages: dict) -> str:
    lines = [f"## Bonsái: {bonsai_name}\n", f"Fecha actual: {current_date}\n"]

    if events:
        lines.append("### Historial de eventos de cultivo")
        for event in events:
            lines.append(f"- {event}")
        lines.append("")

    if existing_plan:
        lines.append("### Plan de fertilización existente en la wiki")
        lines.append(existing_plan)
        lines.append("")

    lines.append("### Fertilizantes disponibles en el catálogo")
    for fertilizer in fertilizers:
        amount = f" (dosis recomendada: {fertilizer.recommended_amount})" if fertilizer.recommended_amount else ""
        lines.append(f"- {fertilizer.name}{amount}")
    lines.append("")

    if fertilizer_pages:
        lines.append("### Fichas técnicas de fertilizantes")
        for name, content in fertilizer_pages.items():
            lines.append(f"#### {name}")
            lines.append(content)
            lines.append("")

    return "\n".join(lines)
