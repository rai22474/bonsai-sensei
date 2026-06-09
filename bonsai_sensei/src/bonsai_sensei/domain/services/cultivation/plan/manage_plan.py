import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from google.adk.workflow import START, Workflow, node
from google.adk.runners import InMemoryRunner
from google.genai import types
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.planned_work import PlannedWork
from bonsai_sensei.domain.services.cultivation.plan.plan_context import bonsai_slug, load_bonsai_plan_context
from bonsai_sensei.domain.services.cultivation.plan.wiki_utils import read_wiki_content, update_wiki_on_abandon
from bonsai_sensei.domain.services.human_input import resolve_bonsai_name
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
    ask_human: Callable,
    build_bonsai_name_question: Callable,
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
        bonsai_name: str | None = None,
        start_date: str = "",
        end_date: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        bonsai_name = await resolve_bonsai_name(bonsai_name, ask_human, build_bonsai_name_question, tool_context)

        outer_tool_context = tool_context

        @node
        async def validate_and_load_context(ctx):
            try:
                date.fromisoformat(start_date)
                date.fromisoformat(end_date)
            except ValueError:
                ctx.state["error"] = "invalid_date_format"
                return "error"

            bonsai = get_bonsai_by_name_func(bonsai_name)
            if not bonsai:
                ctx.state["error"] = "bonsai_not_found"
                return "error"

            bonsai_user_id = bonsai.user_id or "default"
            products = list_products_func(user_id=bonsai_user_id)
            if not products:
                ctx.state["error"] = no_products_error
                return "error"

            existing_plan = get_active_plan_func(bonsai_id=bonsai.id)
            bonsai_context = load_bonsai_plan_context(
                bonsai=bonsai,
                bonsai_name=bonsai_name,
                list_bonsai_events_func=list_bonsai_events_func,
                list_wiki_files_func=list_wiki_files_func,
                read_wiki_page_func=read_wiki_page_func,
            )
            ctx.state["bonsai"] = bonsai
            ctx.state["bonsai_user_id"] = bonsai_user_id
            ctx.state["products"] = products
            ctx.state["bonsai_context"] = bonsai_context
            ctx.state["existing_plan"] = existing_plan
            ctx.state["existing_plan_wiki"] = read_wiki_content(existing_plan.wiki_path, read_wiki_page_func) if existing_plan else ""
            ctx.route = "ok"

        @node
        async def clarify_objectives(ctx):
            products = ctx.state["products"]
            bonsai_context = ctx.state["bonsai_context"]
            reclarify_reason = ctx.state.get("reclarify_reason", "")

            rendered_prompt = clarification_prompt_template.render(
                bonsai_name=bonsai_name,
                start_date=start_date,
                end_date=end_date,
                products=products,
                events=bonsai_context["events"],
                reports=bonsai_context["reports"],
                bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
                active_design_plan_content=bonsai_context.get("active_design_plan_content", ""),
                existing_plan_content=ctx.state.get("existing_plan_wiki", ""),
                reclarify_reason=reclarify_reason,
            )
            clarification = await run_clarification_loop(rendered_prompt, outer_tool_context)

            if clarification.get("cancelled"):
                ctx.state["cancelled"] = True
                ctx.state["cancel_reason"] = "user_cancelled_during_clarification"
                return

            ctx.state["clarification"] = clarification
            ctx.state["reclarify_reason"] = ""
            ctx.route = "ok"

        @node
        async def propose_plan(ctx):
            products = ctx.state["products"]
            bonsai_context = ctx.state["bonsai_context"]
            clarification = ctx.state["clarification"]

            rendered_prompt = plan_proposal_prompt_template.render(
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
                active_design_plan_content=bonsai_context.get("active_design_plan_content", ""),
            )
            proposal = await run_plan_proposal(rendered_prompt, outer_tool_context)

            if proposal.get("cancelled"):
                ctx.state["cancelled"] = True
                ctx.state["cancel_reason"] = proposal.get("reason", "")
                return

            if proposal.get("reclarify"):
                ctx.state["reclarify_reason"] = proposal.get("reason", "")
                ctx.route = "reclarify"
                return

            ctx.state["proposal"] = proposal
            ctx.route = "confirm"

        @node
        async def create_plan(ctx):
            proposal = ctx.state["proposal"]
            clarification = ctx.state["clarification"]
            bonsai = ctx.state["bonsai"]
            bonsai_user_id = ctx.state["bonsai_user_id"]
            existing_plan = ctx.state.get("existing_plan")
            entries = proposal["entries"]
            rationale = proposal["rationale"]
            slug = bonsai_slug(bonsai_name)

            if existing_plan:
                _abandon_existing_plan(existing_plan, delete_future_planned_works_func, update_plan_func, read_wiki_page_func, write_wiki_page_func)

            wiki_path = f"users/{bonsai_user_id}/bonsai/{slug}/{wiki_path_prefix}/{start_date[:7]}_to_{end_date[:7]}.md"
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
            _update_plans_index(bonsai_name, slug, bonsai_user_id, plan, start_date, end_date, wiki_path_prefix, plans_index_wiki_template, write_wiki_page_func)

            ctx.state["plan_result"] = {
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

        wf = Workflow(
            name=f"{tool_name}_wf",
            edges=[
                (START, validate_and_load_context),
                (validate_and_load_context, {"ok": clarify_objectives}),
                (clarify_objectives, {"ok": propose_plan}),
                (propose_plan, {"confirm": create_plan, "reclarify": clarify_objectives}),
            ],
        )
        runner = InMemoryRunner(node=wf)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=runner.app_name,
            session_id=session_id,
        )
        async for _ in runner.run_async(
            user_id=runner.app_name,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text="begin")]),
        ):
            pass

        session = await runner.session_service.get_session(
            app_name=runner.app_name,
            user_id=runner.app_name,
            session_id=session_id,
        )
        state = session.state if session else {}
        if state.get("error"):
            return {"status": "error", "message": state["error"]}
        if state.get("cancelled"):
            return {"status": "cancelled", "reason": state.get("cancel_reason", "")}
        return state.get("plan_result", {"status": "error", "message": "plan_creation_failed"})

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
    user_id: str,
    new_plan,
    period_start: str,
    period_end: str,
    wiki_path_prefix: str,
    plans_index_wiki_template,
    write_wiki_page_func: Callable,
) -> None:
    write_wiki_page_func(
        path=f"users/{user_id}/bonsai/{slug}/{wiki_path_prefix}/index.md",
        content=plans_index_wiki_template.render(
            bonsai_name=bonsai_name,
            plans=[{"period_start": period_start, "period_end": period_end, "status": "active", "wiki_path": new_plan.wiki_path}],
        ),
    )
