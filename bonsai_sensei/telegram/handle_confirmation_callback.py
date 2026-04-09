from telegram import Update
from telegram.ext import ContextTypes
from bonsai_sensei.domain.services.advisor import apply_confirmation_decision
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_confirmation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    confirmation_store=None,
    inject_confirmation_result=None,
):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not confirmation_store:
        await query.edit_message_text("No hay confirmaciones configuradas.")
        return

    parts = (query.data or "").split(":", 2)
    if len(parts) < 3:
        await query.edit_message_text("Confirmación inválida.")
        return

    action, confirmation_id = parts[1], parts[2]
    user_id = str(query.from_user.id)

    confirmation = confirmation_store.pop_pending_by_id(user_id, confirmation_id)
    if not confirmation:
        await query.edit_message_text("Confirmación no encontrada.")
        return

    accepted = action == "accept"
    await apply_confirmation_decision(inject_confirmation_result, user_id, confirmation, accepted)
    response_text = "Confirmación aceptada." if accepted else "Confirmación cancelada."
    await query.edit_message_text(response_text)
