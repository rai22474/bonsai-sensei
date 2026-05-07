from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.fertilization_plan import FertilizationPlan
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.fertilization.context import (
    bonsai_slug,
    load_bonsai_plan_context,
)
from bonsai_sensei.domain.services.cultivation.plan.fertilization.wiki import read_wiki_content, update_wiki_on_abandon
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)
CLARIFICATION_AGENT_PROMPT = _env.get_template("clarification_agent_prompt.j2")
PLAN_PROPOSAL_PROMPT = _env.get_template("plan_proposal_prompt.j2")
PLAN_WIKI_PAGE = _env.get_template("plan_wiki_page.j2")
PLANS_INDEX_WIKI = _env.get_template("plans_index_wiki.j2")


def create_manage_fertilization_plan_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_fertilizers_func: Callable,
    get_fertilizer_by_name_func: Callable,
    get_active_fertilization_plan_func: Callable,
    create_fertilization_plan_func: Callable,
    update_fertilization_plan_func: Callable,
    create_planned_work_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    run_clarification_loop: Callable,
    run_plan_proposal: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def manage_fertilization_plan(
        bonsai_name: str,
        start_date: str,
        end_date: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Create or replace the fertilization plan for a bonsai for a given period. Runs a multi-turn clarification dialogue with the user before generating the plan, then asks for confirmation before persisting. If an active plan already exists, abandons it first.

        Args:
            bonsai_name: Name of the bonsai to plan fertilization for.
            start_date: Start of the planning period in ISO format (YYYY-MM-DD).
            end_date: End of the planning period in ISO format (YYYY-MM-DD).

        Returns:
            A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
            Output JSON (success): {"status": "success", "plan_id": int}.
            Output JSON (cancelled): {"status": "cancelled", "reason": str}.
            Output JSON (error): {"status": "error", "message": str}.
            Error messages: "bonsai_not_found", "no_fertilizers_available", "invalid_date_format".
        """
        try:
            date.fromisoformat(start_date)
            date.fromisoformat(end_date)
        except ValueError:
            return {"status": "error", "message": "invalid_date_format"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        fertilizers = list_fertilizers_func()
        if not fertilizers:
            return {"status": "error", "message": "no_fertilizers_available"}

        existing_plan = get_active_fertilization_plan_func(bonsai_id=bonsai.id)
        slug = bonsai_slug(bonsai_name)
        bonsai_context = load_bonsai_plan_context(
            bonsai=bonsai,
            bonsai_name=bonsai_name,
            list_bonsai_events_func=list_bonsai_events_func,
            list_wiki_files_func=list_wiki_files_func,
            read_wiki_page_func=read_wiki_page_func,
        )

        clarification = await run_clarification_loop(
            rendered_prompt=CLARIFICATION_AGENT_PROMPT.render(
                bonsai_name=bonsai_name,
                start_date=start_date,
                end_date=end_date,
                fertilizers=fertilizers,
                events=bonsai_context["events"],
                bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
                existing_plan_content=read_wiki_content(existing_plan.wiki_path, read_wiki_page_func) if existing_plan else "",
            ),
            outer_tool_context=tool_context,
        )

        proposal = await run_plan_proposal(
            rendered_prompt=PLAN_PROPOSAL_PROMPT.render(
                bonsai_name=bonsai_name,
                start_date=start_date,
                end_date=end_date,
                current_date=date.today().isoformat(),
                objectives=clarification["objectives"],
                preferences=clarification["preferences"],
                context=clarification["context"],
                events=bonsai_context["events"],
                fertilizers=fertilizers,
                fertilizer_pages=_load_fertilizer_wiki_pages(fertilizers, read_wiki_page_func),
                reports=bonsai_context["reports"],
                bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
            ),
            outer_tool_context=tool_context,
        )
        if proposal.get("cancelled"):
            return {"status": "cancelled", "reason": proposal.get("reason", "")}

        entries = proposal["entries"]
        rationale = proposal["rationale"]

        if existing_plan:
            _abandon_plan(existing_plan, delete_future_planned_works_func, update_fertilization_plan_func, read_wiki_page_func, write_wiki_page_func)

        wiki_path = f"bonsai/{slug}/plans/{start_date[:7]}_to_{end_date[:7]}.md"

        plan = create_fertilization_plan_func(
            FertilizationPlan(
                bonsai_id=bonsai.id,
                period_start=date.fromisoformat(start_date),
                period_end=date.fromisoformat(end_date),
                status="active",
                wiki_path=wiki_path,
            )
        )
        _create_planned_works(bonsai.id, plan.id, entries, get_fertilizer_by_name_func, create_planned_work_func)

        write_wiki_page_func(
            path=wiki_path,
            content=PLAN_WIKI_PAGE.render(
                bonsai_name=bonsai_name,
                period_start=start_date,
                period_end=end_date,
                status="active",
                created_at=date.today().isoformat(),
                rationale=rationale,
                entries=entries,
            ),
        )
        _update_plans_index(bonsai_name, slug, plan, start_date, end_date, write_wiki_page_func)

        return {
            "status": "success",
            "plan_id": plan.id,
            "wiki_path": wiki_path,
            "period": f"{start_date} → {end_date}",
            "applications": [
                {
                    "date": entry["date"],
                    "fertilizer": entry["fertilizer_name"],
                    "dose": entry.get("dose", ""),
                }
                for entry in entries
            ],
        }

    return manage_fertilization_plan


def _load_fertilizer_wiki_pages(fertilizers: list, read_wiki_page_func: Callable) -> dict:
    return {
        fertilizer.name: page["content"]
        for fertilizer in fertilizers
        if fertilizer.wiki_path
        and (page := read_wiki_page_func(path=fertilizer.wiki_path)).get("status") == "success"
    }


def _abandon_plan(
    plan: FertilizationPlan,
    delete_future_planned_works_func: Callable,
    update_fertilization_plan_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
) -> None:
    today = date.today()
    delete_future_planned_works_func(plan_id=plan.id, cutoff_date=today)
    plan.status = "abandoned"
    plan.abandonment_reason = "Replaced by new plan"
    plan.abandoned_at = datetime.now(timezone.utc)
    update_fertilization_plan_func(plan)
    update_wiki_on_abandon(plan.wiki_path, plan.abandonment_reason, read_wiki_page_func, write_wiki_page_func)


def _create_planned_works(
    bonsai_id: int,
    plan_id: int,
    entries: list,
    get_fertilizer_by_name_func: Callable,
    create_planned_work_func: Callable,
) -> None:
    for entry in entries:
        fertilizer = get_fertilizer_by_name_func(entry["fertilizer_name"])
        create_planned_work_func(
            PlannedWork(
                bonsai_id=bonsai_id,
                plan_id=plan_id,
                work_type="fertilizer_application",
                payload={
                    "fertilizer_id": fertilizer.id,
                    "fertilizer_name": fertilizer.name,
                    "amount": entry.get("dose", ""),
                },
                scheduled_date=date.fromisoformat(entry["date"]),
                notes=entry.get("notes") or None,
            )
        )


def _update_plans_index(
    bonsai_name: str,
    bonsai_slug: str,
    new_plan: FertilizationPlan,
    period_start: str,
    period_end: str,
    write_wiki_page_func: Callable,
) -> None:
    write_wiki_page_func(
        path=f"bonsai/{bonsai_slug}/plans/index.md",
        content=PLANS_INDEX_WIKI.render(
            bonsai_name=bonsai_name,
            plans=[{"period_start": period_start, "period_end": period_end, "status": "active", "wiki_path": new_plan.wiki_path}],
        ),
    )
