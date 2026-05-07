from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.telegram.messages._formatting import random_processing_message

logger = get_logger(__name__)


async def handle_plan_review_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pending_human_responses: dict | None = None,
    pending_confirmation_cleanups: dict | None = None,
    ask_correction_func: Callable | None = None,
):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    parts = (query.data or "").split(":", 2)
    if len(parts) < 3:
        await query.edit_message_text("Revisión inválida.")
        return

    review_id, action = parts[1], parts[2]
    user_id = str(query.from_user.id)

    if not pending_human_responses:
        await query.edit_message_text("No hay revisión pendiente.")
        return

    pending = pending_human_responses.get(user_id)
    if not pending or pending.get("review_id") != review_id:
        await query.edit_message_text("No hay revisión pendiente.")
        return

    if pending_confirmation_cleanups is not None:
        pending_confirmation_cleanups.setdefault(user_id, []).append(query.message.delete)

    if action == "confirm":
        await query.edit_message_text(random_processing_message())
        pending["response"] = "confirmed"
        pending["event"].set()
        return

    if action == "correct":
        await query.edit_message_text("✏️ Indica los cambios que quieres hacer.")
        pending["response"] = "correct"
        pending["event"].set()
        return

    await query.edit_message_text("❌ Plan cancelado.")
    pending["response"] = "cancelled"
    pending["event"].set()
