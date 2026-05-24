from pathlib import Path
from typing import Callable

import telegram
from telegram import Update
from telegram.ext import ContextTypes

from bonsai_sensei.admin_config import save_review_sessions
from bonsai_sensei.knowledge_base import wiki_git
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)


async def handle_wiki_review_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    wiki_review_sessions: dict | None = None,
    send_page_diff_message: Callable | None = None,
    send_review_status: Callable | None = None,
    wiki_root: str = "./wiki",
    admin_chat_id: str | None = None,
):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    parts = (query.data or "").split(":", 3)
    if len(parts) < 4:
        return

    action, review_id, raw_index = parts[1], parts[2], parts[3]

    if wiki_review_sessions is None:
        return

    session = wiki_review_sessions.get(review_id)
    if not session:
        await query.edit_message_text("Sesión de revisión no encontrada o expirada.")
        return

    try:
        page_index = int(raw_index)
    except ValueError:
        return

    if page_index >= len(session.pending):
        await query.edit_message_text("Página no disponible.")
        return

    page_path = session.pending[page_index]
    chat_id = str(query.message.chat_id)

    if action == "select":
        await query.edit_message_reply_markup(reply_markup=None)
        diff = wiki_git.get_page_diff(Path(wiki_root), page_path, session.commit_hash)
        diff_summary = _format_diff_for_display(diff, page_path)
        if send_page_diff_message:
            await send_page_diff_message(chat_id, page_path, diff_summary, review_id, page_index)
        return

    if action == "confirm":
        session.resolve_page(page_path, reverted=False)
        logger.info("Admin confirmed wiki page %s (review %s)", page_path, review_id)

    elif action == "revert":
        try:
            wiki_git.revert_page(Path(wiki_root), page_path, session.commit_hash)
            session.resolve_page(page_path, reverted=True)
            logger.info("Admin reverted wiki page %s (review %s)", page_path, review_id)
        except Exception as error:
            logger.error("Failed to revert wiki page %s: %s", page_path, error)
            await query.edit_message_text(f"❌ Error al revertir {page_path}.")
            return

    if session.is_complete:
        wiki_review_sessions.pop(review_id, None)

    save_review_sessions(Path(wiki_root), wiki_review_sessions)

    if action == "confirm":
        await query.edit_message_text(f"✅ {page_path} confirmada.")
    elif action == "revert":
        await query.edit_message_text(f"↩️ {page_path} revertida.")

    if send_review_status and admin_chat_id:
        try:
            await send_review_status(admin_chat_id, review_id, session.pending)
        except telegram.error.TelegramError as error:
            logger.error("Failed to send review status: %s", error)


def _format_diff_for_display(diff: str, page_path: str) -> str:
    if not diff.strip():
        return f"Sin cambios detectados en {page_path}."
    added = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    preview_lines = [
        line for line in diff.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ][:20]
    preview = "\n".join(preview_lines)
    return f"+{added} líneas añadidas, -{removed} eliminadas\n\n<pre>{preview}</pre>"
