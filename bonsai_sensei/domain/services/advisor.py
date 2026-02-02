from typing import Callable
from functools import partial
import os
from google.adk.runners import InMemoryRunner, RunConfig
from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from bonsai_sensei.domain.services.tool_limiter import ToolCallsLimitExceededError


DEFAULT_MAX_LLM_CALLS = 20


def create_advisor(
    sensei_agent,
    trace_handler: Callable[[str, list], None] | None = None,
) -> Callable[..., str]:
    runner = InMemoryRunner(agent=sensei_agent, app_name="bonsai_sensei")

    return partial(_generate_advise, runner=runner, trace_handler=trace_handler)


async def _generate_advise(
    text: str,
    runner: InMemoryRunner,
    user_id: str = "default_user",
    trace_handler: Callable[[str, list], None] | None = None,
) -> str:
    run_config = RunConfig(max_llm_calls=DEFAULT_MAX_LLM_CALLS)
    try:
        events = await runner.run_debug(
            user_messages=text,
            user_id=user_id,
            session_id=str(user_id),
            run_config=run_config
        )
    except (LlmCallsLimitExceededError, ToolCallsLimitExceededError):
        return "No pude hacerlo y no tengo la información necesaria."
    if trace_handler:
        trace_handler(text, events)
    response_texts = []
    for event in events:
        if event.content and hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_texts.append(part.text)
    if not response_texts:
        return "No pude generar una respuesta en este momento."
    return "\n".join(response_texts)
