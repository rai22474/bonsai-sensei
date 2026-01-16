from telegram import Update
from telegram.ext import ContextTypes
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.id} started the bot in chat {chat_id}")
    
    await update.message.reply_html(
        f"Hola {user.mention_html()}! Soy Bonsai Sensei Bot.",
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, message_processor=None):
    logger.info(f"Received message from {update.effective_user.id}: {update.message.text}")
    if message_processor:
        response = await message_processor(update.message.text, user_id=str(update.effective_user.id))
    else:
        logger.error("No message processor configured for message handler")
        response = "Error interno: No puedo procesar tu mensaje."
    
    await update.message.reply_text(response)

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
