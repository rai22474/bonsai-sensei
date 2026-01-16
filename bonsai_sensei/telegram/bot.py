import os
from telegram.ext import Application
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class TelegramBot:
    def __init__(self, handlers: list = None, error_handler=None):
        self.application = None
        if TOKEN:
            self.application = Application.builder().token(TOKEN).build()
            if handlers:
                for handler in handlers:
                    self.application.add_handler(handler)
            if error_handler:
                self.application.add_error_handler(error_handler)
        else:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Bot will not function.")

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


