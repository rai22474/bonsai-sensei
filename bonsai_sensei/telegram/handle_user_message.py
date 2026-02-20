from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bonsai_sensei.domain.services.advisor import AdvisorResponse
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_user_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, message_processor=None
):
    logger.info(
        f"Received message from {update.effective_user.id}: {update.message.text}"
    )

    if not message_processor:
        logger.error("No message processor configured for message handler")
        await update.message.reply_text("Error interno: No puedo procesar tu mensaje.")
        return

    response: AdvisorResponse = await message_processor(
        update.message.text, user_id=str(update.effective_user.id)
    )

    await update.message.reply_text(response.text)

    for pending in response.pending_confirmations:
        await update.message.reply_text(
            pending.summary,
            reply_markup=_create_confirmation_keyboard(pending.id),
        )


def _create_confirmation_keyboard(confirmation_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Aceptar", callback_data=f"confirm:accept:{confirmation_id}"),
                InlineKeyboardButton("Cancelar", callback_data=f"confirm:cancel:{confirmation_id}"),
            ]
        ]
    )
