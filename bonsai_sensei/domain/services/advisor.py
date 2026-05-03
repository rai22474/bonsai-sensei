import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable
from functools import partial

from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types
from opentelemetry import metrics, trace

DEFAULT_MAX_LLM_CALLS = 20
MAX_SESSION_EVENTS = 50

_PROGRESS_MESSAGES = {
    "command_pipeline": "🗺️ Elaborando un plan de acción...",
    "gardener": "🌱 Gestionando la colección de bonsáis...",
    "kantei": "🔍 Analizando la foto...",
    "botanist": "🌿 Consultando el herbario de especies...",
    "planning_agent": "📅 Planificando trabajos de cultivo...",
    "weather_advisor": "🌤️ Consultando el pronóstico meteorológico...",
    "storekeeper": "📦 Consultando el catálogo de insumos...",
    "fertilizer_advisor": "🧪 Seleccionando fertilizante...",
    "phytosanitary_advisor": "🛡️ Seleccionando producto fitosanitario...",
}

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


@dataclass
class AdvisorResponse:
    text: str
    photos: list = field(default_factory=list)
    photos_taken_on: list = field(default_factory=list)


def create_advisor(
    sensei_agent,
    get_user_settings_func: Callable | None = None,
) -> tuple[Callable[..., AdvisorResponse], Callable[..., None]]:
    runner = InMemoryRunner(agent=sensei_agent, app_name="bonsai_sensei")

    async def reset_session(user_id: str) -> None:
        await runner.session_service.delete_session(
            app_name="bonsai_sensei",
            user_id=user_id,
            session_id=str(user_id),
        )

    return (
        partial(
            _generate_advise,
            runner=runner,
            get_user_settings_func=get_user_settings_func,
        ),
        reset_session,
    )


async def _generate_advise(
    content: types.Content | str,
    runner: InMemoryRunner,
    user_id: str = "default_user",
    get_user_settings_func: Callable | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> AdvisorResponse:
    state_delta = _build_context_state(user_id, get_user_settings_func)
    await _sync_session(runner, user_id, state_delta)
    message = content if isinstance(content, types.Content) else _build_user_message(content)
    events = await _run_agent(runner, user_id, message, progress_callback)
    photos_taken_on = await _pop_photos_taken_on(runner, user_id)
    response_text = "\n".join(_build_response_texts(events))
    photos = await _collect_and_clear_photos(runner, user_id)
    return AdvisorResponse(text=response_text, photos=photos, photos_taken_on=photos_taken_on)


def _build_context_state(user_id: str, get_user_settings_func: Callable | None) -> dict:
    user_settings = get_user_settings_func(user_id) if get_user_settings_func else None
    user_location = user_settings.location if user_settings and user_settings.location else ""
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7 or 7
    next_saturday = (today + timedelta(days=days_until_saturday)).isoformat()
    return {
        "current_date": today.isoformat(),
        "next_saturday": next_saturday,
        "user_location": user_location,
        "photos_to_display": [],
        "photos_for_analysis_taken_on": [],
    }


async def _sync_session(runner: InMemoryRunner, user_id: str, state_delta: dict) -> None:
    session = await runner.session_service.get_session(
        app_name="bonsai_sensei",
        user_id=user_id,
        session_id=str(user_id),
    )
    if session is not None and len(session.events) > MAX_SESSION_EVENTS:
        await runner.session_service.delete_session(
            app_name="bonsai_sensei",
            user_id=user_id,
            session_id=str(user_id),
        )
        await runner.session_service.create_session(
            app_name="bonsai_sensei",
            user_id=user_id,
            session_id=str(user_id),
            state=state_delta,
        )
        return
    if session is None:
        await runner.session_service.create_session(
            app_name="bonsai_sensei",
            user_id=user_id,
            session_id=str(user_id),
            state=state_delta,
        )
        return
    storage_session = runner.session_service.sessions.get("bonsai_sensei", {}).get(user_id, {}).get(str(user_id))
    if storage_session:
        storage_session.state.update(state_delta)


def _build_user_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


async def _pop_photos_taken_on(runner: InMemoryRunner, user_id: str) -> list:
    session = await runner.session_service.get_session(
        app_name="bonsai_sensei",
        user_id=user_id,
        session_id=str(user_id),
    )
    if session is None:
        return []
    taken_on_list = list(session.state.get("photos_for_analysis_taken_on") or [])
    session.state["photos_for_analysis_taken_on"] = []
    return taken_on_list


async def _run_agent(
    runner: InMemoryRunner,
    user_id: str,
    message: types.Content,
    progress_callback: Callable[[str], None] | None,
) -> list:
    run_config = RunConfig(max_llm_calls=DEFAULT_MAX_LLM_CALLS)
    with _tracer.start_as_current_span("agent.run") as span:
        span.set_attribute("session.id", user_id)
        span.set_attribute("agent.name", "sensei")
        span.set_attribute("model.max_llm_calls", DEFAULT_MAX_LLM_CALLS)
        start_time = time.monotonic()
        events = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=str(user_id),
            new_message=message,
            run_config=run_config,
        ):
            events.append(event)
            if progress_callback:
                progress_text = _extract_progress_message(event)
                if progress_text:
                    await progress_callback(progress_text)
        latency_ms = (time.monotonic() - start_time) * 1000
        span.set_attribute("agent.event_count", len(events))
    _execution_counter.add(1, {"user.id": user_id})
    _execution_latency.record(latency_ms, {"user.id": user_id})
    return events


def _extract_progress_message(event) -> str | None:
    if not (event.content and hasattr(event.content, "parts") and event.content.parts):
        return None
    for part in event.content.parts:
        function_call = getattr(part, "function_call", None)
        if function_call and function_call.name in _PROGRESS_MESSAGES:
            return _PROGRESS_MESSAGES[function_call.name]
    return None


async def _collect_and_clear_photos(runner: InMemoryRunner, user_id: str) -> list[str]:
    session = await runner.session_service.get_session(
        app_name="bonsai_sensei",
        user_id=user_id,
        session_id=str(user_id),
    )
    if session is None:
        return []
    photos = list(session.state.get("photos_to_display") or [])
    session.state["photos_to_display"] = []
    return photos


def _build_response_texts(events: list) -> list[str]:
    response_texts = []

    for event in events:
        if event.content and hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_texts.append(part.text)

    return response_texts
