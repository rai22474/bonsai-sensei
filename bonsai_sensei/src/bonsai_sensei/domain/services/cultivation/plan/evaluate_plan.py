from pathlib import Path
from typing import Callable

from google.adk.tools.tool_context import ToolContext
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.services.cultivation.plan.plan_context import load_bonsai_plan_context
from bonsai_sensei.domain.services.cultivation.plan.plan_evaluation_runner import create_plan_evaluation_runner
from bonsai_sensei.domain.services.cultivation.plan.wiki_utils import read_wiki_content
from bonsai_sensei.domain.services.human_input import resolve_bonsai_name
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_evaluate_plan_tool(
    tool_name: str,
    tool_docstring: str,
    evaluation_instruction: str,
    template_dir: Path,
    model: object,
    get_bonsai_by_name_func: Callable,
    get_active_plan_func: Callable,
    list_bonsai_events_func: Callable,
    read_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    ask_human: Callable,
    build_bonsai_name_question: Callable,
) -> Callable:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    evaluation_prompt = env.get_template("plan_evaluation_prompt.j2")
    run_plan_evaluation = create_plan_evaluation_runner(model=model, instruction=evaluation_instruction)

    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def evaluate_plan(
        bonsai_name: str | None = None,
        new_information: str = "",
        tool_context: ToolContext | None = None,
    ) -> dict:
        bonsai_name = await resolve_bonsai_name(bonsai_name, ask_human, build_bonsai_name_question, tool_context)

        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        active_plan = get_active_plan_func(bonsai_id=bonsai.id)
        if not active_plan:
            return {"status": "error", "message": "no_active_plan"}

        plan_content = read_wiki_content(active_plan.wiki_path, read_wiki_page_func) if active_plan.wiki_path else ""
        bonsai_context = load_bonsai_plan_context(
            bonsai=bonsai,
            bonsai_name=bonsai_name,
            list_bonsai_events_func=list_bonsai_events_func,
            list_wiki_files_func=list_wiki_files_func,
            read_wiki_page_func=read_wiki_page_func,
        )

        rendered = evaluation_prompt.render(
            bonsai_name=bonsai_name,
            plan_content=plan_content,
            events=bonsai_context["events"],
            reports=bonsai_context["reports"],
            bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
            new_information=new_information,
        )
        result = await run_plan_evaluation(rendered)
        return {"status": "success", **result}

    evaluate_plan.__name__ = tool_name
    evaluate_plan.__doc__ = tool_docstring
    return evaluate_plan
