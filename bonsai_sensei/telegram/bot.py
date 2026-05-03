import html
import os
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class TelegramBot:
    def __init__(self, handlers: list = None, error_handler=None):
        self.application = None
        if TOKEN:
            self.application = Application.builder().token(TOKEN).concurrent_updates(True).build()
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

    async def send_confirmation_message(self, chat_id: str, text: str, confirmation_id: str):
        if not self.application:
            logger.error("Cannot send confirmation message: Bot not configured")
            return
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Aceptar", callback_data=f"confirm:accept:{confirmation_id}"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"confirm:cancel:{confirmation_id}"),
        ]])
        await self.application.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)

    async def send_selection_message(self, chat_id: str, question: str, options: list[str], selection_id: str) -> str | None:
        if not self.application:
            logger.error("Cannot send selection message: Bot not configured")
            return None
        none_option = "🚫 Ninguna de las anteriores"
        poll_max_options = 10
        if len(options) < poll_max_options:
            poll_options = [opt[:100] for opt in options] + [none_option]
            message = await self.application.bot.send_poll(
                chat_id=chat_id,
                question=question[:300],
                options=poll_options,
                is_anonymous=False,
                allows_multiple_answers=False,
                type="regular",
            )
            return message.poll.id
        keyboard = InlineKeyboardMarkup([
            *[[InlineKeyboardButton(f"🌿 {option}", callback_data=f"selection:{selection_id}:{index}")]
              for index, option in enumerate(options)],
            [InlineKeyboardButton(none_option, callback_data=f"selection:{selection_id}:none")],
        ])
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=f"<b>{html.escape(question)}</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return None

    async def send_selection_with_photos(
        self,
        chat_id: str,
        question: str,
        options: list[str],
        photo_file_paths: list[str],
        selection_id: str,
    ):
        if not self.application:
            logger.error("Cannot send photo selection: Bot not configured")
            return
        for index, (option, photo_file_path) in enumerate(zip(options, photo_file_paths)):
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(f"✅ {option}", callback_data=f"selection:{selection_id}:{index}")
            ]])
            from pathlib import Path
            path = Path(photo_file_path)
            if path.exists():
                with open(path, "rb") as photo_file:
                    await self.application.bot.send_photo(chat_id=chat_id, photo=photo_file, reply_markup=keyboard)
            else:
                await self.application.bot.send_message(chat_id=chat_id, text=f"🌿 {option}", reply_markup=keyboard)
        cancel_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Ninguna de las anteriores", callback_data=f"selection:{selection_id}:none")
        ]])
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=f"<b>{html.escape(question)}</b>",
            reply_markup=cancel_keyboard,
            parse_mode="HTML",
        )

    async def send_force_reply_message(self, chat_id: str, text: str):
        if not self.application:
            logger.error("Cannot send force reply message: Bot not configured")
            return
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=ForceReply(selective=True, input_field_placeholder="Escribe el motivo..."),
        )


