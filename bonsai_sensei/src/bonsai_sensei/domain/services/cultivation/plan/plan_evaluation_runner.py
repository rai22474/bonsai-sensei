import json
import uuid
from typing import Callable

from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types

_APP_NAME = "plan_evaluator"
_MAX_LLM_CALLS = 3


def create_plan_evaluation_runner(model: object, instruction: str) -> Callable:
    async def run_plan_evaluation(context: str) -> dict:
        agent = Agent(model=model, name=_APP_NAME, instruction=instruction)
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
