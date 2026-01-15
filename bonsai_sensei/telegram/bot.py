import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        f"Hola {user.mention_html()}! Soy Bonsai Sensei Bot.",
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Has dicho: {update.message.text}")

class TelegramBot:
    def __init__(self):
        self.application = None
        if TOKEN:
            self.application = Application.builder().token(TOKEN).build()
            self.add_handlers()
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot will not function.")

    def add_handlers(self):
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    async def initialize(self):
        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

    async def shutdown(self):
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    async def send_message(self, chat_id: str, text: str):
        if not self.application:
             logger.error("Cannot send message: Bot not configured")
             return
        await self.application.bot.send_message(chat_id=chat_id, text=text)


bot = TelegramBot()
