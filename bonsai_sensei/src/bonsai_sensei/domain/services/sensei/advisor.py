from dataclasses import dataclass, field
from typing import Callable, Optional
from functools import partial

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import BaseMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from bonsai_sensei.domain.services.sensei.session_manager import (
    APP_NAME,
    ChannelConfig,
    ACTIVE_CHANNEL_MAIN_STATE_KEY,
    sync_session,
    create_channel_session,
    release_channel_in_main_session,
    sync_handoff_summary_to_main_session,
    inject_handoff_summary,
)
from bonsai_sensei.domain.services.sensei.runner import (
    run_runner,
    pop_state_list,
    build_user_message,
    build_response_texts,
    capture_session_to_memory_safe,
)

COMPACTION_INTERVAL = 5
COMPACTION_OVERLAP = 2


@dataclass
class AdvisorResponse:
    text: str
    photos: list = field(default_factory=list)
    photos_taken_on: list = field(default_factory=list)


def create_advisor(
    default_agent,
    channels: list[ChannelConfig] | None = None,
    progress_messages: dict[str, str] | None = None,
    context_state_builder: Callable[[str], dict] | None = None,
    memory_service: Optional[BaseMemoryService] = None,
) -> tuple[Callable[..., AdvisorResponse], Callable[..., None]]:
    session_service = InMemorySessionService()

    default_app = App(
        name=APP_NAME,
        root_agent=default_agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=COMPACTION_INTERVAL,
            overlap_size=COMPACTION_OVERLAP,
        ),
    )
    default_runner = Runner(
        app=default_app,
        app_name=APP_NAME,
        artifact_service=InMemoryArtifactService(),
        session_service=session_service,
        memory_service=memory_service,
    )

    channel_runners = _build_channel_runners(channels, session_service, default_runner)

    _progress = progress_messages or {}
    _ctx_builder = context_state_builder or (lambda _uid: {})

    async def reset_session(user_id: str) -> None:
        await session_service.delete_session(
            app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
        )
        for channel_cfg, _ in channel_runners.values():
            try:
                await session_service.delete_session(
                    app_name=APP_NAME,
                    user_id=user_id,
                    session_id=channel_cfg.session_id_for(user_id),
                )
            except Exception:
                pass

    return (
        partial(
            _generate_advise,
            default_runner=default_runner,
            channel_runners=channel_runners,
            session_service=session_service,
            progress_messages=_progress,
            context_state_builder=_ctx_builder,
            memory_service=memory_service,
        ),
        reset_session,
    )


async def _generate_advise(
    content: types.Content | str,
    default_runner: Runner,
    channel_runners: dict[str, tuple[ChannelConfig, Runner]],
    session_service,
    user_id: str = "default_user",
    progress_messages: dict[str, str] | None = None,
    context_state_builder: Callable[[str], dict] | None = None,
    progress_callback: Callable[[str], None] | None = None,
    memory_service: Optional[BaseMemoryService] = None,
) -> AdvisorResponse:
    context_state = context_state_builder(user_id) if context_state_builder else {}
    await sync_session(session_service, user_id, context_state)

    message = (
        content if isinstance(content, types.Content) else build_user_message(content)
    )

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
    )
    active_channel = (
        session.state.get(ACTIVE_CHANNEL_MAIN_STATE_KEY) if session else None
    )
    current_channel = active_channel if active_channel in channel_runners else None

    current_runner, current_session_id = _resolve_runner_for_channel(
        current_channel, channel_runners, default_runner, user_id
    )

    events = await run_runner(
        runner=current_runner,
        session_id=current_session_id,
        user_id=user_id,
        message=message,
        progress_callback=progress_callback,
        progress_messages=progress_messages or {},
        record_metrics=(current_channel is None),
    )

    await _handle_channel_transition(
        current_channel=current_channel,
        current_session_id=current_session_id,
        channel_runners=channel_runners,
        session_service=session_service,
        user_id=user_id,
    )

    if memory_service is not None:
        await capture_session_to_memory_safe(session_service, user_id, memory_service)

    return await _collect_response(session_service, user_id, events)


def _build_channel_runners(
    channels: list[ChannelConfig] | None,
    session_service,
    default_runner: Runner,
) -> dict[str, tuple[ChannelConfig, Runner]]:
    result: dict[str, tuple[ChannelConfig, Runner]] = {}
    for channel in channels or []:
        channel_app = App(name=APP_NAME, root_agent=channel.agent)
        channel_runner = Runner(
            app=channel_app,
            app_name=APP_NAME,
            artifact_service=InMemoryArtifactService(),
            session_service=session_service,
        )
        channel_with_callbacks = _wire_channel_callbacks(channel, default_runner)
        result[channel.name] = (channel_with_callbacks, channel_runner)
    return result


def _wire_channel_callbacks(
    channel: ChannelConfig, default_runner: Runner
) -> ChannelConfig:
    if channel.on_enter is None:
        channel.on_enter = partial(_initialize_channel_session, channel=channel)
    if channel.on_exit is None:
        channel.on_exit = partial(
            _handoff_channel_to_default, channel=channel, default_runner=default_runner
        )
    return channel


async def _handle_channel_transition(
    current_channel: str | None,
    current_session_id: str,
    channel_runners: dict[str, tuple[ChannelConfig, Runner]],
    session_service,
    user_id: str,
) -> None:
    check_session = await session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=current_session_id
    )
    new_channel_raw = (
        check_session.state.get(ACTIVE_CHANNEL_MAIN_STATE_KEY)
        if check_session
        else None
    )
    new_channel = new_channel_raw if new_channel_raw in channel_runners else None

    if new_channel == current_channel:
        return
    if current_channel:
        channel_cfg, _ = channel_runners[current_channel]
        if channel_cfg.on_exit:
            await channel_cfg.on_exit(session_service, user_id)
    if new_channel:
        new_cfg, _ = channel_runners[new_channel]
        main_session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=str(user_id)
        )
        if new_cfg.on_enter and main_session:
            await new_cfg.on_enter(session_service, user_id, main_session)


async def _collect_response(
    session_service, user_id: str, events: list
) -> AdvisorResponse:
    photos_taken_on = await pop_state_list(
        session_service, user_id, "photos_for_analysis_taken_on"
    )
    photos = await pop_state_list(session_service, user_id, "photos_to_display")
    return AdvisorResponse(
        text="\n".join(build_response_texts(events)),
        photos=photos,
        photos_taken_on=photos_taken_on,
    )


def _resolve_runner_for_channel(
    current_channel: str | None,
    channel_runners: dict[str, tuple[ChannelConfig, Runner]],
    default_runner: Runner,
    user_id: str,
) -> tuple[Runner, str]:
    if current_channel:
        channel_cfg, channel_runner = channel_runners[current_channel]
        return channel_runner, channel_cfg.session_id_for(user_id)
    return default_runner, str(user_id)


async def _initialize_channel_session(
    session_service, user_id: str, main_session, *, channel: ChannelConfig
) -> None:
    await create_channel_session(session_service, user_id, channel, main_session)


async def _handoff_channel_to_default(
    session_service, user_id: str, *, channel: ChannelConfig, default_runner: Runner
) -> None:
    await sync_handoff_summary_to_main_session(
        session_service, user_id, channel.session_id_for(user_id)
    )
    await release_channel_in_main_session(session_service, user_id)
    await inject_handoff_summary(default_runner, session_service, user_id)
