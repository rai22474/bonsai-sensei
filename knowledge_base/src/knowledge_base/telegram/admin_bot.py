import asyncio
import uuid
from functools import partial
from pathlib import Path
from typing import Callable, Optional

import telegram
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters

from knowledge_base.admin_config import save_admin_chat_id, save_review_sessions
from knowledge_base.wiki_review_session import WikiReviewSession
from knowledge_base.wiki_index.indexer import build_full_index
from knowledge_base.logging_config import get_logger
from knowledge_base.telegram.handle_admin_ingest import handle_admin_ingest

_logger = get_logger(__name__)

_YOUTUBE_URL_PATTERN = r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[a-zA-Z0-9_-]{11}"


class AdminBotManager:
    def __init__(
        self,
        bot,
        wiki_root: Path,
        wiki_review_sessions: dict,
        run_wiki_dreamer: Callable,
        ingest_transcript: Callable,
        wiki_review_handler: Callable,
        fetch_channel_slug: Optional[Callable] = None,
        wiki_editor: Optional[Callable] = None,
        embed: Optional[Callable] = None,
        save_entry: Optional[Callable] = None,
    ):
        self._bot = bot
        self._wiki_root = wiki_root
        self._wiki_review_sessions = wiki_review_sessions
        self._run_wiki_dreamer = run_wiki_dreamer
        self._ingest_transcript = ingest_transcript
        self._wiki_review_handler = wiki_review_handler
        self._fetch_channel_slug = fetch_channel_slug
        self._wiki_editor = wiki_editor
        self._embed = embed
        self._save_entry = save_entry
        self._chat_id: str | None = None

    def set_chat_id(self, chat_id: str | None) -> None:
        self._chat_id = chat_id

    def set_run_wiki_dreamer(self, run_wiki_dreamer: Callable) -> None:
        self._run_wiki_dreamer = run_wiki_dreamer

    def set_ingest_transcript(self, ingest_transcript: Callable) -> None:
        self._ingest_transcript = ingest_transcript

    def set_fetch_channel_slug(self, fetch_channel_slug: Callable) -> None:
        self._fetch_channel_slug = fetch_channel_slug

    @property
    def chat_id(self) -> str | None:
        return self._chat_id

    def build_handlers(self) -> list:
        admin_ingest_handler = partial(
            handle_admin_ingest,
            ingest_transcript=self._ingest_transcript,
            fetch_channel_slug=self._fetch_channel_slug,
        )

        async def admin_start_command(update, context):
            chat_id = str(update.effective_chat.id)
            save_admin_chat_id(self._wiki_root, chat_id)
            self._chat_id = chat_id
            _logger.info("Admin chat_id registered: %s", chat_id)
            await update.message.reply_text("✅ Admin registrado. Ya puedes recibir notificaciones del wiki dreamer.")

        async def dreamer_command(update, context):
            chat_id = str(update.effective_chat.id)
            await update.message.reply_text("🌙 Lanzando wiki dreamer...")
            task = asyncio.create_task(self._run_dreamer_and_notify(chat_id))
            task.add_done_callback(self._log_task_exception)

        async def index_command(update, context):
            if self._embed is None or self._save_entry is None:
                await update.message.reply_text("⚠️ El indexador no está configurado.")
                return
            await update.message.reply_text("🔍 Indexando wiki...")
            count = await build_full_index(self._wiki_root, self._embed, self._save_entry)
            await update.message.reply_text(f"✅ Índice construido: {count} páginas indexadas.")

        async def ingest_command(update, context):
            args = update.message.text.removeprefix("/ingest").strip()
            if not args:
                await update.message.reply_text("Uso: /ingest <youtube_url> [canal]")
                return
            await handle_admin_ingest(
                update, context,
                ingest_transcript=self._ingest_transcript,
                fetch_channel_slug=self._fetch_channel_slug,
                text_override=args,
            )

        async def feedback_command(update, context):
            feedback_text = update.message.text.removeprefix("/feedback").strip()
            if not feedback_text:
                await update.message.reply_text("Uso: /feedback <corrección a incorporar en la wiki>")
                return
            from knowledge_base.dreamer.memory_reader import append_admin_correction
            append_admin_correction(self._wiki_root, feedback_text)
            await update.message.reply_text("✅ Corrección guardada. Se incorporará en la próxima pasada del dreamer.")

        async def wiki_editor_handler(update, telegram_context):
            if self._wiki_editor is None:
                await update.message.reply_text("El editor de wiki no está disponible.")
                return
            chat_id = str(update.effective_chat.id)
            text = update.message.text or ""
            thinking_message = await update.message.reply_text("⏳ Pensando...")

            async def keep_typing():
                steps = ["⏳ Pensando...", "🔍 Buscando en la wiki...", "✍️ Editando páginas...", "💾 Guardando cambios..."]
                step_index = 0
                while True:
                    await asyncio.sleep(6)
                    step_index = (step_index + 1) % len(steps)
                    try:
                        await thinking_message.edit_text(steps[step_index])
                    except Exception:
                        pass

            typing_task = asyncio.create_task(keep_typing())
            try:
                response = await self._wiki_editor(chat_id, text)
            finally:
                typing_task.cancel()
                await thinking_message.delete()
            await update.message.reply_text(response, parse_mode="HTML")

        return [
            CommandHandler("start", admin_start_command),
            CommandHandler("dreamer", dreamer_command),
            CommandHandler("index", index_command),
            CommandHandler("ingest", ingest_command),
            CommandHandler("feedback", feedback_command),
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.Regex(_YOUTUBE_URL_PATTERN),
                admin_ingest_handler,
            ),
            MessageHandler(filters.TEXT & ~filters.COMMAND, wiki_editor_handler),
            CallbackQueryHandler(self._wiki_review_handler, pattern=r"^wiki:(select|confirm|revert):.+:\d+$"),
        ]

    async def notify_wiki_changes(self, changed_files: list[str], commit_hash: str) -> None:
        if not self._chat_id:
            return
        reviewable = [path for path in changed_files if path.endswith(".md")]
        if not reviewable:
            return
        review_id = uuid.uuid4().hex[:8]
        session = WikiReviewSession(
            review_id=review_id,
            commit_hash=commit_hash,
            pending=reviewable,
        )
        self._wiki_review_sessions[review_id] = session
        save_review_sessions(self._wiki_root, self._wiki_review_sessions)
        try:
            await self._bot.send_wiki_review_notification(
                chat_id=self._chat_id,
                changed_files=reviewable,
                review_id=review_id,
            )
        except telegram.error.TelegramError as error:
            _logger.error("Failed to notify admin of wiki changes: %s", error)

    async def re_notify_pending_sessions(self) -> None:
        _logger.info(
            "re_notify_pending_sessions: chat_id=%s sessions=%d",
            self._chat_id,
            len(self._wiki_review_sessions),
        )
        if not self._chat_id:
            _logger.warning("re_notify_pending_sessions: no chat_id, skipping")
            return
        if not self._wiki_review_sessions:
            _logger.info("re_notify_pending_sessions: no sessions, nothing to re-notify")
            return
        for session in self._wiki_review_sessions.values():
            _logger.info(
                "re_notify_pending_sessions: session=%s pending=%d pages",
                session.review_id,
                len(session.pending),
            )
            if not session.pending:
                continue
            try:
                await self._bot.send_wiki_review_notification(
                    chat_id=self._chat_id,
                    changed_files=session.pending,
                    review_id=session.review_id,
                )
            except telegram.error.TelegramError as error:
                _logger.error("Failed to re-notify pending review session %s: %s", session.review_id, error)

    async def _run_dreamer_and_notify(self, chat_id: str) -> None:
        await self._run_wiki_dreamer()
        await self.re_notify_pending_sessions()
        try:
            await self._bot.send_message(chat_id=chat_id, text="✅ Wiki dreamer completado.")
        except telegram.error.TelegramError as error:
            _logger.error("Failed to send dreamer completion notification: %s", error)

    def _log_task_exception(self, task):
        if not task.cancelled() and task.exception():
            _logger.error("Background task failed: %s", task.exception())
