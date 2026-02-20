from dataclasses import dataclass, field
from typing import Callable
from functools import partial
from google.adk.runners import InMemoryRunner, RunConfig

from bonsai_sensei.domain.confirmation_store import ConfirmationStore

DEFAULT_MAX_LLM_CALLS = 20


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
) -> Callable[..., AdvisorResponse]:
    runner = InMemoryRunner(agent=sensei_agent, app_name="bonsai_sensei")

    return partial(_generate_advise, runner=runner, confirmation_store=confirmation_store)


async def _generate_advise(
    text: str,
    runner: InMemoryRunner,
    user_id: str = "default_user",
    confirmation_store: ConfirmationStore | None = None,
) -> AdvisorResponse:
    run_config = RunConfig(max_llm_calls=DEFAULT_MAX_LLM_CALLS)

    events = await runner.run_debug(
        user_messages=text,
        user_id=user_id,
        session_id=str(user_id),
        run_config=run_config,
    )

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
