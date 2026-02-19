from telegram import Update
from telegram.ext import ContextTypes
from bonsai_sensei.logging_config import get_logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = get_logger(__name__)


async def handle_user_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, message_processor=None
):
    logger.info(
        f"Received message from {update.effective_user.id}: {update.message.text}"
    )

    if not message_processor:
        logger.error("No message processor configured for message handler")
        response = "Error interno: No puedo procesar tu mensaje."

    response = await message_processor(
        update.message.text, user_id=str(update.effective_user.id)
    )

    if isinstance(response, str):
        if response.requires_confirmation:
            await update.message.reply_text(response.text, 
                                            reply_markup=_create_confirmation_keyboard())
            return
        
        await update.message.reply_text(response.text)
        return
    
    await update.message.reply_text(response)


def _create_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Aceptar", callback_data="confirm:accept"),
                    InlineKeyboardButton(
                        "Cancelar", callback_data="confirm:cancel"
                    ),
                ]
            ]
        )

    return keyboard
