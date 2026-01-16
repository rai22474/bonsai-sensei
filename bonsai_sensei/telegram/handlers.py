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
