import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable
from functools import partial

from google.adk.runners import InMemoryRunner, RunConfig
from google.genai import types
from opentelemetry import metrics, trace

from bonsai_sensei.domain.confirmation_store import ConfirmationStore

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


@dataclass
class PendingConfirmationInfo:
    id: str
    summary: str


@dataclass
class AdvisorResponse:
    text: str
    pending_confirmations: list[PendingConfirmationInfo] = field(default_factory=list)


def create_advisor(
    sensei_agent,
    confirmation_store: ConfirmationStore | None = None,
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
            confirmation_store=confirmation_store,
            get_user_settings_func=get_user_settings_func,
        ),
        reset_session,
    )


async def _generate_advise(
    text: str,
    runner: InMemoryRunner,
    user_id: str = "default_user",
    confirmation_store: ConfirmationStore | None = None,
    get_user_settings_func: Callable | None = None,
) -> AdvisorResponse:
    run_config = RunConfig(max_llm_calls=DEFAULT_MAX_LLM_CALLS)

    user_settings = get_user_settings_func(user_id) if get_user_settings_func else None
    user_location = user_settings.location if user_settings and user_settings.location else ""

    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7 or 7
    next_saturday = (today + timedelta(days=days_until_saturday)).isoformat()

    state_delta = {
        "current_date": today.isoformat(),
        "next_saturday": next_saturday,
        "user_location": user_location,
    }

    session = await runner.session_service.get_session(
        app_name="bonsai_sensei",
        user_id=user_id,
        session_id=str(user_id),
    )
    if session is None:
        await runner.session_service.create_session(
            app_name="bonsai_sensei",
            user_id=user_id,
            session_id=str(user_id),
            state=state_delta,
        )
    else:
        session.state.update(state_delta)

    new_message = types.Content(role="user", parts=[types.Part(text=text)])

    with _tracer.start_as_current_span("agent.run") as span:
        span.set_attribute("session.id", user_id)
        span.set_attribute("agent.name", "sensei")
        span.set_attribute("model.max_llm_calls", DEFAULT_MAX_LLM_CALLS)
        start_time = time.monotonic()
        events = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=str(user_id),
            new_message=new_message,
            run_config=run_config,
        ):
            events.append(event)
        latency_ms = (time.monotonic() - start_time) * 1000
        span.set_attribute("agent.event_count", len(events))

    _execution_counter.add(1, {"user.id": user_id})
    _execution_latency.record(latency_ms, {"user.id": user_id})

    response_text = "\n".join(_build_response_texts(events))

    if not confirmation_store:
        return AdvisorResponse(text=response_text)

    unsent_confirmations = confirmation_store.get_unsent(user_id)
    for confirmation in unsent_confirmations:
        confirmation.sent = True

    pending_confirmations = [
        PendingConfirmationInfo(id=confirmation.id, summary=confirmation.summary)
        for confirmation in unsent_confirmations
    ]

    return AdvisorResponse(text=response_text, pending_confirmations=pending_confirmations)


def _build_response_texts(events: list) -> list[str]:
    response_texts = []

    for event in events:
        if event.content and hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_texts.append(part.text)

    return response_texts
