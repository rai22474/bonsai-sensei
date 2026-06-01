from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_poll_answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pending_human_responses: dict | None = None,
    poll_id_to_user_id: dict | None = None,
    send_free_text_prompt: Callable | None = None,
):
    """Handle a Telegram PollAnswer update for clarification polls."""
    poll_answer = update.poll_answer
    if not poll_answer:
        return

    poll_id = poll_answer.poll_id
    option_ids = poll_answer.option_ids

    if not option_ids:
        return

    if not poll_id_to_user_id or not pending_human_responses:
        return

    user_id = poll_id_to_user_id.get(poll_id)
    if not user_id:
        return

    pending = pending_human_responses.get(user_id)
    if not pending or pending.get("type") not in ("poll", "awaiting_poll_free_text"):
        return

    options = pending.get("options", [])
    selected_index = option_ids[0]
    free_text_index = len(options)

    if selected_index == free_text_index:
        pending["type"] = "awaiting_poll_free_text"
        if send_free_text_prompt:
            await send_free_text_prompt(user_id, "¿Qué tenías en mente? Escríbelo:")
        return

    try:
        selected_option = options[selected_index]
    except IndexError:
        logger.error("Poll answer index %d out of range for options %s", selected_index, options)
        return

    pending["response"] = selected_option
    pending["event"].set()
