from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

POLL_NONE_OPTION_TEXT = "🚫 Ninguna de las anteriores"


async def handle_poll_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pending_human_responses: dict | None = None,
    send_none_reason_prompt: Callable | None = None,
):
    """Process a Telegram poll vote and resolve the pending selection."""
    poll_answer = update.poll_answer
    if not poll_answer:
        return

    user_id = str(poll_answer.user.id)
    poll_id = poll_answer.poll_id

    if not pending_human_responses:
        return

    pending = pending_human_responses.get(user_id)
    if not pending or pending.get("poll_id") != poll_id:
        logger.warning("Received poll answer for unknown poll_id=%s from user=%s", poll_id, user_id)
        return

    if not poll_answer.option_ids:
        return

    options = pending.get("options", [])
    selected_index = poll_answer.option_ids[0]

    if selected_index == len(options):
        pending["type"] = "awaiting_none_reason"
        if send_none_reason_prompt:
            await send_none_reason_prompt(user_id, "¿Por qué ninguna de las opciones es correcta?")
        return

    try:
        selected = options[selected_index]
    except IndexError:
        logger.error("Poll answer index %d out of range for options %s", selected_index, options)
        return

    pending["response"] = selected
    pending["event"].set()
