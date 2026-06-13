from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.runners import Runner, RunConfig
from google.genai import types

APP_NAME = "bonsai_sensei"
LAST_ACTIVITY_STATE_KEY = "last_activity_at"
INACTIVITY_THRESHOLD_HOURS = 8
HANDOFF_SUMMARY_STATE_KEY = "channel_handoff_summary"
ACTIVE_CHANNEL_MAIN_STATE_KEY = "active_channel"


@dataclass
class ChannelConfig:
    """Declares a secondary conversation channel that can take over the user's session.

    When an agent sets state[active_channel] = name, subsequent messages route to this
    channel's runner until the channel releases control (sets active_channel to None).

    on_enter: called when the channel is activated (after sensei turn that triggered it).
    on_exit:  called when the channel releases control (after a channel turn).
    """
    name: str
    agent: object
    session_id_for: Callable[[str], str]
    state_init_prefix: str = ""
    on_enter: Optional[Callable] = field(default=None, compare=False)
    on_exit: Optional[Callable] = field(default=None, compare=False)


async def commit_state(session_service, session, delta: dict) -> None:
    """Persists a state delta to a session via the ADK event mechanism."""
    event = Event(
        invocation_id="advisor",
        author="advisor",
        actions=EventActions(state_delta=delta),
    )
    await session_service.append_event(session, event)


async def sync_session(session_service, user_id: str, state_delta: dict) -> None:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    if session is not None and _is_stale(session):
        await session_service.delete_session(
            app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
        )
        session = None
    if session is None:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=str(user_id),
            state=state_delta,
        )
        return
    await commit_state(session_service, session, state_delta)


def _is_stale(session) -> bool:
    last_activity_raw = session.state.get(LAST_ACTIVITY_STATE_KEY)
    if last_activity_raw is None:
        return False
    last_activity = datetime.fromisoformat(last_activity_raw)
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - last_activity > timedelta(hours=INACTIVITY_THRESHOLD_HOURS)


async def create_channel_session(
    session_service, user_id: str, channel_cfg: ChannelConfig, main_session
) -> None:
    channel_session_id = channel_cfg.session_id_for(user_id)
    existing = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=channel_session_id
    )
    if existing is None:
        initial_state = {
            k: v for k, v in main_session.state.items()
            if channel_cfg.state_init_prefix and k.startswith(channel_cfg.state_init_prefix)
        }
        initial_state[ACTIVE_CHANNEL_MAIN_STATE_KEY] = channel_cfg.name
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=channel_session_id,
            state=initial_state,
        )


async def release_channel_in_main_session(session_service, user_id: str) -> None:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    if session is not None:
        await commit_state(session_service, session, {ACTIVE_CHANNEL_MAIN_STATE_KEY: None})


async def sync_handoff_summary_to_main_session(
    session_service, user_id: str, channel_session_id: str
) -> None:
    channel_session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=channel_session_id
    )
    if channel_session is None:
        return
    summary = channel_session.state.get(HANDOFF_SUMMARY_STATE_KEY)
    if not summary:
        return
    main_session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    if main_session is not None:
        await commit_state(session_service, main_session, {HANDOFF_SUMMARY_STATE_KEY: summary})


async def inject_handoff_summary(runner: Runner, session_service, user_id: str) -> None:
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    if session is None:
        return
    summary = session.state.get(HANDOFF_SUMMARY_STATE_KEY)
    if not summary:
        return
    async for _ in runner.run_async(
        user_id=user_id,
        session_id=str(user_id),
        new_message=types.Content(role="user", parts=[types.Part(text=f"[sistema] {summary}")]),
        run_config=RunConfig(max_llm_calls=4),
    ):
        pass
    refreshed = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    if refreshed is not None:
        await commit_state(session_service, refreshed, {HANDOFF_SUMMARY_STATE_KEY: None})
