import uuid
from typing import Callable

from google.adk.agents import LoopAgent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import InMemoryRunner, RunConfig
from google.adk.tools.tool_context import ToolContext
from google.genai import types

_MAX_ITERATIONS = 5


def create_clarification_loop_runner(model: object, ask_human: Callable, app_name: str, ask_poll: Callable | None = None) -> Callable:
    async def run_clarification_loop(rendered_prompt: str, outer_tool_context) -> dict:
        async def ask_user_question(question: str) -> str:
            """Ask the user an open clarification question and wait for their text response. Use when the answer space is completely open-ended."""
            return await ask_human(question, tool_context=outer_tool_context)

        async def ask_user_with_poll(question: str, options: list[str]) -> str:
            """Ask the user a clarification question as a Telegram poll with selectable options you provide.

            Use when you can anticipate the most likely answers. Provide short, mutually exclusive
            option labels (max 6 options, each max 90 characters, in the user's language).
            The user can also choose to write a free-text answer instead.

            Args:
                question: The clarification question (max 300 characters).
                options: Short option labels. Max 6 items, each max 90 characters.

            Returns:
                The selected option text, or the user's free-text response.
            """
            return await ask_poll(question, options, tool_context=outer_tool_context)

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

        if ask_poll is not None:
            tools = [ask_user_question, ask_user_with_poll, finalize_clarification]
        else:
            tools = [ask_user_question, finalize_clarification]

        inner_agent = LlmAgent(
            name="clarifier",
            model=model,
            instruction=rendered_prompt,
            tools=tools,
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
