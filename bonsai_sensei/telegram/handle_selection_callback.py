from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_selection_callback(
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

    options = pending.get("options", [])
    try:
        selected = options[int(index_str)]
    except (ValueError, IndexError):
        await query.edit_message_text("Opción no válida.")
        return

    pending["response"] = selected
    pending["event"].set()
    await query.edit_message_text(f"Seleccionado: {selected}")
