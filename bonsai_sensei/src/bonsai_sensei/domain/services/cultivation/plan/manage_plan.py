from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.plan_context import bonsai_slug, load_bonsai_plan_context
from bonsai_sensei.domain.services.cultivation.plan.wiki_utils import read_wiki_content, update_wiki_on_abandon
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_manage_plan_tool(
    tool_name: str,
    tool_docstring: str,
    plan_class: type,
    no_products_error: str,
    wiki_path_prefix: str,
    plan_id_kwarg: str,
    work_type: str,
    product_id_key: str,
    product_name_key: str,
    product_response_label: str,
    template_dir: Path,
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_products_func: Callable,
    get_product_by_name_func: Callable,
    get_active_plan_func: Callable,
    create_plan_func: Callable,
    update_plan_func: Callable,
    create_planned_work_func: Callable,
    delete_future_planned_works_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    run_clarification_loop: Callable,
    run_plan_proposal: Callable,
) -> Callable:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    clarification_prompt_template = env.get_template("clarification_agent_prompt.j2")
    plan_proposal_prompt_template = env.get_template("plan_proposal_prompt.j2")
    plan_wiki_page_template = env.get_template("plan_wiki_page.j2")
    plans_index_wiki_template = env.get_template("plans_index_wiki.j2")

    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def manage_plan(
        bonsai_name: str,
        start_date: str,
        end_date: str,
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

        products = list_products_func()
        if not products:
            return {"status": "error", "message": no_products_error}

        existing_plan = get_active_plan_func(bonsai_id=bonsai.id)
        slug = bonsai_slug(bonsai_name)
        bonsai_context = load_bonsai_plan_context(
            bonsai=bonsai,
            bonsai_name=bonsai_name,
            list_bonsai_events_func=list_bonsai_events_func,
            list_wiki_files_func=list_wiki_files_func,
            read_wiki_page_func=read_wiki_page_func,
        )

        clarification = await run_clarification_loop(
            rendered_prompt=clarification_prompt_template.render(
                bonsai_name=bonsai_name,
                start_date=start_date,
                end_date=end_date,
                products=products,
                events=bonsai_context["events"],
                bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
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
                objectives=clarification["objectives"],
                preferences=clarification["preferences"],
                context=clarification["context"],
                events=bonsai_context["events"],
                products=products,
                product_pages=_load_product_wiki_pages(products, read_wiki_page_func),
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
            _abandon_existing_plan(existing_plan, delete_future_planned_works_func, update_plan_func, read_wiki_page_func, write_wiki_page_func)

        wiki_path = f"bonsai/{slug}/{wiki_path_prefix}/{start_date[:7]}_to_{end_date[:7]}.md"

        plan = create_plan_func(
            plan_class(
                bonsai_id=bonsai.id,
                period_start=date.fromisoformat(start_date),
                period_end=date.fromisoformat(end_date),
                status="active",
                goal=clarification["objectives"],
                wiki_path=wiki_path,
            )
        )
        _create_planned_works(
            bonsai_id=bonsai.id,
            plan_id=plan.id,
            entries=entries,
            plan_id_kwarg=plan_id_kwarg,
            work_type=work_type,
            product_id_key=product_id_key,
            product_name_key=product_name_key,
            get_product_by_name_func=get_product_by_name_func,
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
                rationale=rationale,
                entries=entries,
            ),
        )
        _update_plans_index(bonsai_name, slug, plan, start_date, end_date, wiki_path_prefix, plans_index_wiki_template, write_wiki_page_func)

        return {
            "status": "success",
            "plan_id": plan.id,
            "wiki_path": wiki_path,
            "period": f"{start_date} → {end_date}",
            "applications": [
                {
                    "date": entry["date"],
                    product_response_label: entry[product_name_key],
                    "dose": entry.get("dose", ""),
                }
                for entry in entries
            ],
        }

    manage_plan.__name__ = tool_name
    manage_plan.__doc__ = tool_docstring
    return manage_plan


def _load_product_wiki_pages(products: list, read_wiki_page_func: Callable) -> dict:
    return {
        product.name: page["content"]
        for product in products
        if product.wiki_path
        and (page := read_wiki_page_func(path=product.wiki_path)).get("status") == "success"
    }


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
    plan_id_kwarg: str,
    work_type: str,
    product_id_key: str,
    product_name_key: str,
    get_product_by_name_func: Callable,
    create_planned_work_func: Callable,
) -> None:
    for entry in entries:
        product = get_product_by_name_func(entry[product_name_key])
        create_planned_work_func(
            PlannedWork(
                bonsai_id=bonsai_id,
                **{plan_id_kwarg: plan_id},
                work_type=work_type,
                payload={
                    product_id_key: product.id,
                    product_name_key: product.name,
                    "amount": entry.get("dose", ""),
                },
                scheduled_date=date.fromisoformat(entry["date"]),
                notes=entry.get("notes") or None,
            )
        )


def _update_plans_index(
    bonsai_name: str,
    slug: str,
    new_plan,
    period_start: str,
    period_end: str,
    wiki_path_prefix: str,
    plans_index_wiki_template,
    write_wiki_page_func: Callable,
) -> None:
    write_wiki_page_func(
        path=f"bonsai/{slug}/{wiki_path_prefix}/index.md",
        content=plans_index_wiki_template.render(
            bonsai_name=bonsai_name,
            plans=[{"period_start": period_start, "period_end": period_end, "status": "active", "wiki_path": new_plan.wiki_path}],
        ),
    )
