import logging
import time
from typing import Callable, Optional

from google.adk.memory import BaseMemoryService
from google.adk.runners import Runner, RunConfig
from google.genai import types
from opentelemetry import metrics, trace

APP_NAME = "bonsai_sensei"
DEFAULT_MAX_LLM_CALLS = 20

_tracer = trace.get_tracer(__name__)
_meter = metrics.get_meter(__name__)
_execution_counter = _meter.create_counter(
    "agent.execution.count",
    description="Number of agent executions",
)
_execution_latency = _meter.create_histogram(
    "agent.execution.latency",
    unit="ms",
    description="Agent execution latency in milliseconds",
)


async def run_runner(
    runner: Runner,
    session_id: str,
    user_id: str,
    message: types.Content,
    progress_callback: Callable[[str], None] | None,
    progress_messages: dict[str, str],
    record_metrics: bool = False,
) -> list:
    run_config = RunConfig(max_llm_calls=DEFAULT_MAX_LLM_CALLS)
    with _tracer.start_as_current_span("agent.run") as span:
        span.set_attribute("session.id", user_id)
        span.set_attribute("model.max_llm_calls", DEFAULT_MAX_LLM_CALLS)
        start_time = time.monotonic()
        events = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
            run_config=run_config,
        ):
            events.append(event)
            if progress_callback:
                progress_text = extract_progress_message(event, progress_messages)
                if progress_text:
                    await progress_callback(progress_text)
        latency_ms = (time.monotonic() - start_time) * 1000
        span.set_attribute("agent.event_count", len(events))
    if record_metrics:
        _execution_counter.add(1, {"user.id": user_id})
        _execution_latency.record(latency_ms, {"user.id": user_id})
    return events


def extract_progress_message(event, progress_messages: dict[str, str]) -> str | None:
    if not (event.content and hasattr(event.content, "parts") and event.content.parts):
        return None
    for part in event.content.parts:
        function_call = getattr(part, "function_call", None)
        if function_call and function_call.name in progress_messages:
            return progress_messages[function_call.name]
    return None


async def pop_state_list(session_service, user_id: str, state_key: str) -> list:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    if session is None:
        return []
    items = list(session.state.get(state_key) or [])
    session.state[state_key] = []
    return items


def build_user_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def build_response_texts(events: list) -> list[str]:
    response_texts = []
    for event in events:
        if event.content and hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_texts.append(part.text)
    return response_texts


async def capture_session_to_memory_safe(
    session_service, user_id: str, memory_service: BaseMemoryService
) -> None:
    try:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
        )
        if session is not None:
            await memory_service.add_session_to_memory(session)
    except Exception:
        logging.exception("Memory capture failed for user_id=%s", user_id)
