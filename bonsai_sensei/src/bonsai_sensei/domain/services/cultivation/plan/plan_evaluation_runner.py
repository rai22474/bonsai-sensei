import json
from typing import Callable

from google.genai import types

from bonsai_sensei.domain.services.extract_text_from_events import extract_text_from_events
from bonsai_sensei.domain.services.llm_runner import create_single_turn_llm_runner

_APP_NAME = "plan_evaluator"
_MAX_LLM_CALLS = 3


def create_plan_evaluation_runner(model: object, instruction: str) -> Callable:
    run_llm = create_single_turn_llm_runner(
        model=model,
        app_name=_APP_NAME,
        instruction=instruction,
        max_llm_calls=_MAX_LLM_CALLS,
    )

    async def run_plan_evaluation(context: str) -> dict:
        message = types.Content(role="user", parts=[types.Part(text=context)])
        raw = await extract_text_from_events(run_llm(message))
        return json.loads(raw)

    return run_plan_evaluation
