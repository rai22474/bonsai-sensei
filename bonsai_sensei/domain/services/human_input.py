import asyncio
import uuid
from typing import Callable

from google.adk.tools.tool_context import ToolContext

from bonsai_sensei.domain.services.resolve_user_id import resolve_confirmation_user_id

DEFAULT_TIMEOUT_SECONDS = 300


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
    ) -> bool:
        """Ask the human user a yes/no confirmation question and wait for their answer.

        Sends the question with accept/cancel options and blocks execution until
        the user responds. Returns True if accepted, False if cancelled.
        Confirmations for the same user are serialized: if two tools request
        confirmation simultaneously, the second waits until the first is resolved.

        Args:
            question: The confirmation prompt to present to the user.
            tool_context: ADK tool context providing the user identifier.
            user_id: Explicit user identifier, takes precedence over tool_context.

        Returns:
            True if the user accepted, False if the user cancelled.
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
