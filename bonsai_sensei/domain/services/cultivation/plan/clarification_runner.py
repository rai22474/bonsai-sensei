import uuid
from typing import Callable

from google.adk.agents import LoopAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import InMemoryRunner, RunConfig
from google.adk.tools.tool_context import ToolContext
from google.genai import types

_MAX_ITERATIONS = 5


def create_clarification_loop_runner(model: object, ask_human: Callable, app_name: str) -> Callable:
    async def run_clarification_loop(rendered_prompt: str, outer_tool_context) -> dict:
        async def ask_user_question(question: str) -> str:
            """Ask the user a clarification question. Call this once per question."""
            return await ask_human(question, tool_context=outer_tool_context)

        async def finalize_clarification(
            objectives: str,
            preferences: str,
            context: str,
            tool_context: ToolContext,
            cancelled: bool = False,
        ) -> str:
            """Signal that clarification is complete. Call with cancelled=True if the user explicitly says they do not want to continue. Otherwise call when you have clear objectives, preferences, and context to build the plan."""
            tool_context.actions.escalate = True
            tool_context.state["clarification_result"] = {
                "objectives": objectives,
                "preferences": preferences,
                "context": context,
                "cancelled": cancelled,
            }
            return "cancelled" if cancelled else "ready"

        inner_agent = LlmAgent(
            name="clarifier",
            model=model,
            instruction=rendered_prompt,
            tools=[ask_user_question, finalize_clarification],
        )
        loop = LoopAgent(
            name=app_name,
            sub_agents=[inner_agent],
            max_iterations=_MAX_ITERATIONS,
        )
        runner = InMemoryRunner(agent=loop, app_name=app_name)
        session_id = str(uuid.uuid4())
        await runner.session_service.create_session(
            app_name=app_name, user_id=app_name, session_id=session_id
        )
        message = types.Content(role="user", parts=[types.Part(text="Begin")])
        async for _ in runner.run_async(
            user_id=app_name,
            session_id=session_id,
            new_message=message,
            run_config=RunConfig(max_llm_calls=_MAX_ITERATIONS * 3),
        ):
            pass

        session = await runner.session_service.get_session(
            app_name=app_name, user_id=app_name, session_id=session_id
        )
        result = session.state.get("clarification_result", {})
        return {
            "objectives": result.get("objectives", ""),
            "preferences": result.get("preferences", "no preference"),
            "context": result.get("context", "none"),
            "cancelled": result.get("cancelled", False),
        }

    return run_clarification_loop
