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