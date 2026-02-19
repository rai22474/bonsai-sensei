from telegram import Update
from telegram.ext import ContextTypes
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_confirmation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    confirmation_store=None,
):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if not confirmation_store:
        await query.edit_message_text("No hay confirmaciones configuradas.")
        return

    decision = query.data or ""
    accepted = decision == "confirm:accept"

    response_text = _resolve_confirmation(
        str(query.from_user.id),
        accepted,
        confirmation_store,
    )

    await query.edit_message_text(response_text)


def _resolve_confirmation(user_id: str, accepted: bool, confirmation_store):
    if accepted:
        return "Confirmación aceptada."
    return "Confirmación cancelada."
