import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id

DEFAULT_TIMEOUT_SECONDS = 300


@dataclass
class SelectionNoneResult:
    reason: str


@dataclass
class ConfirmationResult:
    accepted: bool
    reason: str = field(default="")

    def __bool__(self) -> bool:
        return self.accepted


def create_ask_human(
    send_message_func: Callable,
    pending_responses: dict,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Callable:
    async def ask_human(
        question: str,
        tool_context: ToolContext | None = None,
    ) -> str:
        """Ask the human user an open question and wait for their text response.

        Sends the question to the user and blocks execution until they reply.
        The calling agent resumes with the user's text response.

        Args:
            question: The question or prompt to present to the user.
            tool_context: ADK tool context providing the user identifier.

        Returns:
            The user's text response.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        event = asyncio.Event()
        pending_responses[user_id] = {"event": event, "response": None, "type": "text"}
        await send_message_func(user_id, question)
        await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
        return pending_responses.pop(user_id)["response"]

    return ask_human


def create_ask_confirmation(
    send_confirmation_func: Callable,
    pending_responses: dict,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Callable:
    confirmation_locks: dict[str, asyncio.Lock] = {}

    async def ask_confirmation(
        question: str,
        tool_context: ToolContext | None = None,
        user_id: str | None = None,
    ) -> ConfirmationResult:
        """Ask the human user a yes/no confirmation question and wait for their answer.

        Sends the question with accept/cancel options and blocks execution until
        the user responds. Evaluates as truthy if accepted, falsy if cancelled.
        An optional cancellation reason is available via result.reason.
        Confirmations for the same user are serialized: if two tools request
        confirmation simultaneously, the second waits until the first is resolved.

        Args:
            question: The confirmation prompt to present to the user.
            tool_context: ADK tool context providing the user identifier.
            user_id: Explicit user identifier, takes precedence over tool_context.

        Returns:
            ConfirmationResult — truthy if accepted, falsy if cancelled.
        """
        resolved_user_id = user_id or resolve_confirmation_user_id(tool_context)
        if resolved_user_id not in confirmation_locks:
            confirmation_locks[resolved_user_id] = asyncio.Lock()
        async with confirmation_locks[resolved_user_id]:
            confirmation_id = uuid.uuid4().hex
            event = asyncio.Event()
            pending_responses[resolved_user_id] = {
                "event": event,
                "response": None,
                "type": "confirmation",
                "confirmation_id": confirmation_id,
                "summary": question,
            }
            await send_confirmation_func(resolved_user_id, question, confirmation_id)
            try:
                await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
            except TimeoutError:
                pending_responses.pop(resolved_user_id, None)
                raise
            return pending_responses.pop(resolved_user_id)["response"]

    return ask_confirmation


def create_ask_selection(
    send_selection_func: Callable,
    pending_responses: dict,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    send_photo_selection_func: Callable | None = None,
) -> Callable:
    async def ask_selection(
        question: str,
        options: list[str],
        tool_context: ToolContext | None = None,
        photos: list[str] | None = None,
    ) -> str | SelectionNoneResult:
        """Present a list of options to the user and wait for their selection.

        Sends the options as an interactive selector and blocks execution until
        the user picks one or selects "Ninguna de las anteriores".
        When photos are provided and send_photo_selection_func is configured, each
        photo is sent with its corresponding selection button attached, so the user
        can see the image and tap its button in one step.

        Args:
            question: The prompt explaining what the user should select.
            options: The list of options to present.
            tool_context: ADK tool context providing the user identifier.
            photos: Optional list of photo file paths, one per option.

        Returns:
            The selected option string, or SelectionNoneResult if the user
            indicated none of the options were appropriate.
        """
        user_id = resolve_confirmation_user_id(tool_context)
        selection_id = uuid.uuid4().hex
        event = asyncio.Event()
        pending_responses[user_id] = {
            "event": event,
            "response": None,
            "type": "selection",
            "selection_id": selection_id,
            "question": question,
            "options": options,
        }
        if send_photo_selection_func and photos and len(photos) == len(options):
            await send_photo_selection_func(user_id, question, options, photos, selection_id)
        else:
            await send_selection_func(user_id, question, options, selection_id)
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout_seconds)
        except TimeoutError:
            pending_responses.pop(user_id, None)
            raise
        return pending_responses.pop(user_id)["response"]

    return ask_selection
