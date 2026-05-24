import html
import os
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

class TelegramBot:
    def __init__(self, token: str | None = None, handlers: list = None, error_handler=None):
        self.application = None
        resolved_token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if resolved_token:
            self.application = Application.builder().token(resolved_token).concurrent_updates(True).build()
            if handlers:
                for handler in handlers:
                    self.application.add_handler(handler)
            if error_handler:
                self.application.add_error_handler(error_handler)
        else:
            logger.warning("No bot token provided. Bot will not function.")

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
        await self.application.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="HTML")

    async def send_selection_message(self, chat_id: str, question: str, options: list[str], selection_id: str):
        if not self.application:
            logger.error("Cannot send selection message: Bot not configured")
            return
        option_emojis = ["⚡", "📅", "🌸", "🍂", "🍃", "🌾", "🎋", "🌿"]
        keyboard = InlineKeyboardMarkup([
            *[[InlineKeyboardButton(f"{option_emojis[index % len(option_emojis)]} {option}", callback_data=f"selection:{selection_id}:{index}")]
              for index, option in enumerate(options)],
            [InlineKeyboardButton("🚫 Ninguna de las anteriores", callback_data=f"selection:{selection_id}:none")],
        ])
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=f"<b>{html.escape(question)}</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

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

    async def send_plan_review_message(self, chat_id: str, text: str, review_id: str):
        if not self.application:
            logger.error("Cannot send plan review message: Bot not configured")
            return
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirmar", callback_data=f"plan_review:{review_id}:confirm"),
            InlineKeyboardButton("✏️ Corregir", callback_data=f"plan_review:{review_id}:correct"),
            InlineKeyboardButton("❌ Cancelar", callback_data=f"plan_review:{review_id}:cancel"),
        ]])
        await self.application.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="HTML")

    async def send_force_reply_message(self, chat_id: str, text: str):
        if not self.application:
            logger.error("Cannot send force reply message: Bot not configured")
            return
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=ForceReply(selective=True, input_field_placeholder="Escribe el motivo..."),
        )

    async def send_wiki_review_notification(self, chat_id: str, changed_files: list[str], review_id: str) -> None:
        if not self.application:
            logger.error("Cannot send wiki review notification: Bot not configured")
            return
        lines = ["📝 <b>El dreamer actualizó estas páginas:</b>"]
        for page_path in changed_files:
            lines.append(f"• {html.escape(page_path)}")
        text = "\n".join(lines)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔍 {page_path}", callback_data=f"wiki:select:{review_id}:{index}")]
            for index, page_path in enumerate(changed_files)
        ])
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    async def send_wiki_page_diff_message(
        self,
        chat_id: str,
        page_path: str,
        diff_summary: str,
        review_id: str,
        page_index: int,
    ) -> None:
        if not self.application:
            logger.error("Cannot send wiki page diff message: Bot not configured")
            return
        text = f"📄 <b>{html.escape(page_path)}</b>\n\n{html.escape(diff_summary)}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Confirmar", callback_data=f"wiki:confirm:{review_id}:{page_index}"),
            InlineKeyboardButton("↩️ Revertir", callback_data=f"wiki:revert:{review_id}:{page_index}"),
        ]])
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    async def send_wiki_review_status(self, chat_id: str, review_id: str, pending: list[str]) -> None:
        if not self.application:
            logger.error("Cannot send wiki review status: Bot not configured")
            return
        if not pending:
            await self.application.bot.send_message(
                chat_id=chat_id,
                text="✅ <b>Revisión completada.</b>",
                parse_mode="HTML",
            )
            return
        lines = ["📋 <b>Páginas pendientes de revisión:</b>"]
        for page_path in pending:
            lines.append(f"• {html.escape(page_path)}")
        text = "\n".join(lines)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔍 {page_path}", callback_data=f"wiki:select:{review_id}:{index}")]
            for index, page_path in enumerate(pending)
        ])
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    async def send_poll_message(self, chat_id: str, question: str, options: list[str]) -> str:
        """Send a native Telegram poll and return the poll_id."""
        if not self.application:
            logger.error("Cannot send poll: Bot not configured")
            return ""
        all_options = options + ["✏️ Escribir mi propia respuesta"]
        message = await self.application.bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=all_options,
            is_anonymous=False,
            allows_multiple_answers=False,
        )
        return message.poll.id


