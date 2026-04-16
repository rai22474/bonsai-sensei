from telegram import Update
from telegram.ext import ContextTypes
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_confirmation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    pending_human_responses: dict | None = None,
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
    accepted = action == "accept"

    if pending_human_responses:
        pending = pending_human_responses.get(user_id)
        if pending and pending.get("confirmation_id") == confirmation_id:
            pending["response"] = accepted
            pending["event"].set()
            response_text = "Confirmación aceptada." if accepted else "Confirmación cancelada."
            await query.edit_message_text(response_text)
            return

    await query.edit_message_text("No hay confirmación pendiente.")
