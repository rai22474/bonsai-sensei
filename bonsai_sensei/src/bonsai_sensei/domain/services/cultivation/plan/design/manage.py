import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.development_plan import DevelopmentPlan
from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.plan_context import bonsai_slug, load_bonsai_plan_context
from bonsai_sensei.domain.services.cultivation.plan.wiki_utils import read_wiki_content, update_wiki_on_abandon
from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_DOCSTRING = """Create or replace the design development plan for a bonsai for a given period. Runs a multi-turn clarification dialogue with the user before generating the seasonal work calendar, then asks for confirmation before persisting. If an active plan already exists, abandons it first.

Args:
    bonsai_name: Name of the bonsai to plan for.
    start_date: Start of the planning period in ISO format (YYYY-MM-DD).
    end_date: End of the planning period in ISO format (YYYY-MM-DD).
    development_path: Development path of the bonsai (e.g. "planton", "yamadori", "vivero", "nebari").
    current_phase: Current development phase (e.g. "engorde", "aclimatacion", "estructura", "refinamiento").
    target_style: Target bonsai style — must be a slug from wiki design/ (e.g. "moyogi", "bunjin", "kengai").
    design_goal: Free-text description of the artistic objective for this period.

Returns:
    A JSON-ready dictionary with status 'success', 'cancelled', or 'error'.
    Output JSON (success): {"status": "success", "plan_id": int}.
    Output JSON (cancelled): {"status": "cancelled", "reason": str}.
    Output JSON (error): {"status": "error", "message": str}.
    Error messages: "bonsai_not_found", "invalid_date_format".
"""

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_manage_development_plan_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    get_active_development_plan_func: Callable,
    create_development_plan_func: Callable,
    update_development_plan_func: Callable,
    create_planned_work_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    get_species_by_id_func: Callable,
    get_user_settings_func: Callable,
    run_clarification_loop: Callable,
    run_plan_proposal: Callable,
) -> Callable:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    clarification_prompt_template = env.get_template("clarification_agent_prompt.j2")
    plan_proposal_prompt_template = env.get_template("plan_proposal_prompt.j2")
    plan_wiki_page_template = env.get_template("plan_wiki_page.j2")
    plans_index_wiki_template = env.get_template("plans_index_wiki.j2")

    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def manage_development_plan(
        bonsai_name: str,
        start_date: str,
        end_date: str,
        development_path: str,
        current_phase: str,
        target_style: str,
        design_goal: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        try:
            date.fromisoformat(start_date)
            date.fromisoformat(end_date)
        except ValueError:
            return {"status": "error", "message": "invalid_date_format"}

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        existing_plan = get_active_development_plan_func(bonsai_id=bonsai.id)
        slug = bonsai_slug(bonsai_name)
        bonsai_context = load_bonsai_plan_context(
            bonsai=bonsai,
            bonsai_name=bonsai_name,
            list_bonsai_events_func=list_bonsai_events_func,
            list_wiki_files_func=list_wiki_files_func,
            read_wiki_page_func=read_wiki_page_func,
        )

        species_wiki_content = _load_species_wiki(bonsai, get_species_by_id_func, read_wiki_page_func)
        style_wiki_content = _load_style_wiki(target_style, read_wiki_page_func)
        available_techniques = _list_technique_names(list_wiki_files_func)
        user_location = _get_user_location(tool_context, get_user_settings_func)

        recent_reports = _filter_current_year_reports(
            bonsai_name=bonsai_name,
            bonsai_user_id=bonsai.user_id or "default",
            all_reports=bonsai_context["reports"],
            list_wiki_files_func=list_wiki_files_func,
        )

        clarification = await run_clarification_loop(
            rendered_prompt=clarification_prompt_template.render(
                bonsai_name=bonsai_name,
                start_date=start_date,
                end_date=end_date,
                development_path=development_path,
                current_phase=current_phase,
                target_style=target_style,
                design_goal=design_goal,
                bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
                species_wiki_content=species_wiki_content,
                style_wiki_content=style_wiki_content,
                reports=recent_reports,
                events=bonsai_context["events"],
                existing_plan_content=read_wiki_content(existing_plan.wiki_path, read_wiki_page_func) if existing_plan else "",
            ),
            outer_tool_context=tool_context,
        )

        if clarification.get("cancelled"):
            return {"status": "cancelled", "reason": "user_cancelled_during_clarification"}

        proposal = await run_plan_proposal(
            rendered_prompt=plan_proposal_prompt_template.render(
                bonsai_name=bonsai_name,
                start_date=start_date,
                end_date=end_date,
                current_date=date.today().isoformat(),
                development_path=development_path,
                current_phase=current_phase,
                target_style=target_style,
                design_goal=design_goal,
                tree_state=clarification.get("objectives", ""),
                constraints=clarification.get("preferences", ""),
                context=clarification.get("context", ""),
                events=bonsai_context["events"],
                species_wiki_content=species_wiki_content,
                style_wiki_content=style_wiki_content,
                reports=bonsai_context["reports"],
                available_techniques=available_techniques,
                user_location=user_location,
            ),
            outer_tool_context=tool_context,
        )
        if proposal.get("cancelled"):
            return {"status": "cancelled", "reason": proposal.get("reason", "")}

        entries = proposal["entries"]
        rationale = proposal["rationale"]

        if existing_plan:
            _abandon_existing_plan(existing_plan, delete_future_planned_works_func, update_development_plan_func, read_wiki_page_func, write_wiki_page_func)

        bonsai_user_id = bonsai.user_id or "default"
        wiki_path = f"users/{bonsai_user_id}/bonsai/{slug}/design-plans/{start_date[:7]}_to_{end_date[:7]}.md"

        plan = create_development_plan_func(
            DevelopmentPlan(
                bonsai_id=bonsai.id,
                development_path=development_path,
                current_phase=current_phase,
                target_style=target_style,
                design_goal=design_goal,
                period_start=date.fromisoformat(start_date),
                period_end=date.fromisoformat(end_date),
                status="active",
                wiki_path=wiki_path,
            )
        )
        _create_planned_works(
            bonsai_id=bonsai.id,
            plan_id=plan.id,
            entries=entries,
            create_planned_work_func=create_planned_work_func,
        )

        write_wiki_page_func(
            path=wiki_path,
            content=plan_wiki_page_template.render(
                bonsai_name=bonsai_name,
                period_start=start_date,
                period_end=end_date,
                status="active",
                created_at=date.today().isoformat(),
                development_path=development_path,
                current_phase=current_phase,
                target_style=target_style,
                design_goal=design_goal,
                rationale=rationale,
                entries=entries,
            ),
        )
        _update_plans_index(bonsai_name, slug, bonsai_user_id, plan, start_date, end_date, plans_index_wiki_template, write_wiki_page_func)

        return {
            "status": "success",
            "plan_id": plan.id,
            "wiki_path": wiki_path,
            "period": f"{start_date} → {end_date}",
            "works": [
                {"date": entry["date"], "technique": entry["technique_name"]}
                for entry in entries
            ],
        }

    manage_development_plan.__doc__ = _DOCSTRING
    return manage_development_plan


def _load_species_wiki(bonsai, get_species_by_id_func: Callable, read_wiki_page_func: Callable) -> str:
    species = get_species_by_id_func(species_id=bonsai.species_id)
    if species and species.wiki_path:
        page = read_wiki_page_func(path=species.wiki_path)
        if page.get("status") == "success":
            return page["content"]
    return ""


def _load_style_wiki(target_style: str, read_wiki_page_func: Callable) -> str:
    wiki_path = f"design/{target_style}.md"
    page = read_wiki_page_func(path=wiki_path)
    if page.get("status") == "success":
        return page["content"]
    return ""


def _list_technique_names(list_wiki_files_func: Callable) -> list[str]:
    paths = list_wiki_files_func("techniques/")
    return [
        path.replace("techniques/", "").replace(".md", "")
        for path in paths
    ]


def _get_user_location(tool_context, get_user_settings_func: Callable) -> str:
    user_id = resolve_confirmation_user_id(tool_context)
    if not user_id:
        return "unknown"
    settings = get_user_settings_func(user_id)
    if settings and settings.location:
        return settings.location
    return "unknown"


def _abandon_existing_plan(
    plan,
    delete_future_planned_works_func: Callable,
    update_plan_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
) -> None:
    today = date.today()
    delete_future_planned_works_func(plan_id=plan.id, cutoff_date=today)
    plan.status = "abandoned"
    plan.abandonment_reason = "Replaced by new plan"
    plan.abandoned_at = datetime.now(timezone.utc)
    update_plan_func(plan)
    update_wiki_on_abandon(plan.wiki_path, plan.abandonment_reason, read_wiki_page_func, write_wiki_page_func)


def _create_planned_works(
    bonsai_id: int,
    plan_id: int,
    entries: list,
    create_planned_work_func: Callable,
) -> None:
    for entry in entries:
        create_planned_work_func(
            PlannedWork(
                bonsai_id=bonsai_id,
                development_plan_id=plan_id,
                work_type=entry["technique_name"],
                payload={
                    "technique_name": entry["technique_name"],
                    "wiki_path": f"techniques/{entry['technique_name']}.md",
                    "notes": entry.get("notes", ""),
                },
                scheduled_date=date.fromisoformat(entry["date"]),
                notes=entry.get("notes") or None,
            )
        )


_YEAR_PREFIX_RE = re.compile(r"^(\d{4})-")


def _filter_current_year_reports(bonsai_name: str, bonsai_user_id: str, all_reports: list[str], list_wiki_files_func: Callable) -> list[str]:
    """Returns only reports whose filename starts with the current year, or undated reports.
    Reports from previous years are excluded — the tree's state may have changed significantly."""
    current_year = str(date.today().year)
    slug = bonsai_slug(bonsai_name)
    paths = list_wiki_files_func(f"users/{bonsai_user_id}/bonsai/{slug}/reports")

    recent_paths = set()
    for path in paths:
        filename = path.split("/")[-1]
        match = _YEAR_PREFIX_RE.match(filename)
        if match and match.group(1) != current_year:
            continue
        recent_paths.add(path)

    if len(recent_paths) == len(paths):
        return all_reports

    recent_count = len(recent_paths)
    return all_reports[-recent_count:] if recent_count else []


def _update_plans_index(
    bonsai_name: str,
    slug: str,
    user_id: str,
    plan: DevelopmentPlan,
    period_start: str,
    period_end: str,
    plans_index_wiki_template,
    write_wiki_page_func: Callable,
) -> None:
    write_wiki_page_func(
        path=f"users/{user_id}/bonsai/{slug}/design-plans/index.md",
        content=plans_index_wiki_template.render(
            bonsai_name=bonsai_name,
            plans=[{
                "period_start": period_start,
                "period_end": period_end,
                "current_phase": plan.current_phase,
                "target_style": plan.target_style,
                "status": "active",
                "wiki_path": plan.wiki_path,
            }],
        ),
    )
