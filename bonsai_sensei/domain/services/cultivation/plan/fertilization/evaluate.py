import json
import uuid
from pathlib import Path
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from jinja2 import Environment, FileSystemLoader

from bonsai_sensei.domain.services.cultivation.plan.fertilization.context import load_bonsai_plan_context
from bonsai_sensei.domain.services.cultivation.plan.fertilization.wiki import read_wiki_content
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls
from bonsai_sensei.domain.services.tool_tracer import trace_tool_call

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)
PLAN_EVALUATION_PROMPT = _env.get_template("plan_evaluation_prompt.j2")

_APP_NAME = "plan_evaluator"
_MAX_LLM_CALLS = 3

_INSTRUCTION = """
Eres un experto en fertilización de bonsáis. Se te proporciona el plan de fertilización activo y nueva información relevante.
Evalúa críticamente si el plan sigue siendo adecuado a la luz de esa nueva información.

Analiza:
- ¿La nueva información cambia las necesidades del bonsái?
- ¿Alguna aplicación próxima debería modificarse (dosis, producto, fecha)?
- ¿Es necesario replantear el plan completo?

Devuelve ÚNICAMENTE un JSON válido con este formato exacto, sin texto adicional:
{
  "verdict": "ok" | "adjust" | "replace",
  "summary": "<una o dos frases con la evaluación general>",
  "suggestions": ["<sugerencia concreta 1>", "<sugerencia concreta 2>"]
}

- "ok": el plan sigue siendo válido tal cual.
- "adjust": el plan es válido pero necesita ajustes puntuales (indica cuáles en suggestions).
- "replace": la nueva información cambia el contexto lo suficiente como para recomendar un nuevo plan.
- suggestions puede ser lista vacía si verdict es "ok".
"""


def create_plan_evaluation_runner(model: object) -> Callable:
    async def run_plan_evaluation(context: str) -> dict:
        agent = Agent(model=model, name=_APP_NAME, instruction=_INSTRUCTION)
        runner = InMemoryRunner(agent=agent, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id
        )
        message = types.Content(role="user", parts=[types.Part(text=context)])
        response_parts = []
        async for event in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            if event.content and hasattr(event.content, "parts"):
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_parts.append(part.text)
        return json.loads("\n".join(response_parts))

    return run_plan_evaluation


def create_evaluate_fertilization_plan_tool(
    get_bonsai_by_name_func: Callable,
    get_active_fertilization_plan_func: Callable,
    list_bonsai_events_func: Callable,
    read_wiki_page_func: Callable,
    list_wiki_files_func: Callable,
    run_plan_evaluation: Callable,
) -> Callable:
    @trace_tool_call
    @limit_tool_calls(agent_name="kikaru")
    async def evaluate_fertilization_plan(
        bonsai_name: str,
        new_information: str,
        tool_context: ToolContext | None = None,
    ) -> dict:
        """Evaluate the active fertilization plan against new information without modifying it.

        Args:
            bonsai_name: Name of the bonsai whose plan to evaluate.
            new_information: New observations or events that may affect the plan (e.g. health issue, temperature change, growth note).

        Returns:
            A JSON-ready dict with the evaluation.
            Output JSON (success): {"status": "success", "verdict": "ok|adjust|replace", "summary": str, "suggestions": list[str]}.
            Output JSON (error): {"status": "error", "message": str}.
            Error messages: "bonsai_not_found", "no_active_plan".
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        active_plan = get_active_fertilization_plan_func(bonsai_id=bonsai.id)
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

        rendered = PLAN_EVALUATION_PROMPT.render(
            bonsai_name=bonsai_name,
            plan_content=plan_content,
            events=bonsai_context["events"],
            reports=bonsai_context["reports"],
            bonsai_wiki_content=bonsai_context["bonsai_wiki_content"],
            new_information=new_information,
        )
        result = await run_plan_evaluation(rendered)
        return {"status": "success", **result}

    return evaluate_fertilization_plan
