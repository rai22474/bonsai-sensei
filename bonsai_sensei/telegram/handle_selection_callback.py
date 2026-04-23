from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.telegram.messages._formatting import random_processing_message

logger = get_logger(__name__)


async def handle_selection_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pending_human_responses: dict | None = None,
    pending_confirmation_cleanups: dict | None = None,
    send_none_reason_prompt: Callable | None = None,
):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    parts = (query.data or "").split(":", 2)
    if len(parts) < 3:
        await query.edit_message_text("Selección inválida.")
        return

    selection_id, index_str = parts[1], parts[2]
    user_id = str(query.from_user.id)

    if not pending_human_responses:
        await query.edit_message_text("No hay selección pendiente.")
        return

    pending = pending_human_responses.get(user_id)
    if not pending or pending.get("selection_id") != selection_id:
        await query.edit_message_text("No hay selección pendiente.")
        return

    if index_str == "none":
        pending["type"] = "awaiting_none_reason"
        await query.edit_message_text("Ninguna de las anteriores. 🚫")
        if pending_confirmation_cleanups is not None:
            pending_confirmation_cleanups.setdefault(user_id, []).append(query.message.delete)
        if send_none_reason_prompt:
            await send_none_reason_prompt(user_id, "¿Por qué ninguna de las opciones es correcta?")
        return

    options = pending.get("options", [])
    try:
        selected = options[int(index_str)]
    except (ValueError, IndexError):
        await query.edit_message_text("Opción no válida.")
        return

    if pending_confirmation_cleanups is not None:
        pending_confirmation_cleanups.setdefault(user_id, []).append(query.message.delete)

    await query.edit_message_text(random_processing_message())
    pending["response"] = selected
    pending["event"].set()
