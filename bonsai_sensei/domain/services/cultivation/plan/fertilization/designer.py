import json
import uuid
from typing import Callable

from google.adk.agents import LoopAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import InMemoryRunner, RunConfig
from google.adk.tools.tool_context import ToolContext
from google.genai import types

_APP_NAME = "fertilization_plan_proposal"
_MAX_ITERATIONS = 5
_MAX_LLM_CALLS = _MAX_ITERATIONS * 3


def create_fertilization_plan_runner(model: object, ask_human: Callable, ask_confirmation: Callable) -> Callable:
    async def run_plan_proposal(rendered_prompt: str, outer_tool_context) -> dict:
        async def show_proposal_to_user(message: str) -> str:
            """Muestra el plan de fertilización al usuario para confirmación. Devuelve 'confirmed' si el usuario acepta, o 'rechazado: <motivo>' si rechaza."""
            result = await ask_confirmation(message, tool_context=outer_tool_context)
            if result:
                return "confirmed"
            if result.reason:
                return f"rechazado: {result.reason}"
            feedback = await ask_human("¿Qué cambios quieres hacer al plan?", tool_context=outer_tool_context)
            return f"rechazado: {feedback}"

        async def finalize_plan(entries_json: str, rationale: str, tool_context: ToolContext) -> str:
            """Finalize the plan after the user confirms it. entries_json must be a valid JSON array of schedule entries."""
            tool_context.actions.escalate = True
            tool_context.state["proposal_result"] = {
                "entries": json.loads(entries_json),
                "rationale": rationale,
            }
            return "finalized"

        async def cancel_plan(reason: str, tool_context: ToolContext) -> str:
            """Cancel plan creation when the user requests it."""
            tool_context.actions.escalate = True
            tool_context.state["proposal_result"] = {"cancelled": True, "reason": reason}
            return "cancelled"

        inner_agent = LlmAgent(
            name="planner",
            model=model,
            instruction=rendered_prompt,
            tools=[show_proposal_to_user, finalize_plan, cancel_plan],
        )
        loop = LoopAgent(
            name=_APP_NAME,
            sub_agents=[inner_agent],
            max_iterations=_MAX_ITERATIONS,
        )
        runner = InMemoryRunner(agent=loop, app_name=_APP_NAME)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id
        )
        message = types.Content(role="user", parts=[types.Part(text="Begin")])
        async for _ in runner.run_async(
            user_id=_APP_NAME,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_LLM_CALLS),
        ):
            pass

        session = await runner.session_service.get_session(
            app_name=_APP_NAME, user_id=_APP_NAME, session_id=session_id
        )
        return session.state.get("proposal_result", {"cancelled": True, "reason": "max_iterations_reached"})

    return run_plan_proposal
