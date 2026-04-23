from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.domain.services.human_input import ConfirmationResult
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_confirmation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pending_human_responses: dict | None = None,
    send_cancel_reason_prompt: Callable | None = None,
):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    parts = (query.data or "").split(":", 2)
    if len(parts) < 3:
        await query.edit_message_text("Confirmación inválida.")
        return

    action, confirmation_id = parts[1], parts[2]
    user_id = str(query.from_user.id)

    if not pending_human_responses:
        await query.edit_message_text("No hay confirmación pendiente.")
        return

    pending = pending_human_responses.get(user_id)
    if not pending or pending.get("confirmation_id") != confirmation_id:
        await query.edit_message_text("No hay confirmación pendiente.")
        return

    if action == "accept":
        pending["response"] = ConfirmationResult(accepted=True)
        pending["event"].set()
        await query.edit_message_text("Confirmación aceptada. ✅")
        return

    pending["type"] = "awaiting_cancel_reason"
    await query.edit_message_text("Cancelando...")
    if send_cancel_reason_prompt:
        await send_cancel_reason_prompt(user_id, "¿Cuál es el motivo de la cancelación?")
