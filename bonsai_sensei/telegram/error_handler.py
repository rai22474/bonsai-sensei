from telegram import Update
from telegram.ext import ContextTypes
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Lo siento mucho, ha ocurrido un error inesperado."
            )
        except Exception as e:
            logger.error(f"Could not send error response to user: {e}")