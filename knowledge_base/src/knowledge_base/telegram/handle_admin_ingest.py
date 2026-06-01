import asyncio
import os
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from knowledge_base.ingestion.transcript_loader import extract_video_id
from knowledge_base.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_CHANNEL = os.getenv("WIKI_DEFAULT_CHANNEL", "general")


async def handle_admin_ingest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    ingest_transcript: Callable,
) -> None:
    text = (update.message.text or "").strip()
    parts = text.split()
    raw_url = parts[0]
    channel = parts[1] if len(parts) > 1 else _DEFAULT_CHANNEL

    try:
        video_id = extract_video_id(raw_url)
        url = f"https://www.youtube.com/watch?v={video_id}"
    except ValueError:
        await update.message.reply_text(f"❌ No puedo extraer el video ID de: {raw_url}")
        return

    await update.message.reply_text(f"⚙️ Ingesting {video_id} (canal: {channel})...")
    logger.info("Admin triggered ingestion: video_id=%s channel=%s", video_id, channel)

    def _log_task_exception(task):
        if not task.cancelled() and task.exception():
            logger.error("Ingestion task failed for %s: %s", video_id, task.exception())

    task = asyncio.create_task(ingest_transcript(url, channel))
    task.add_done_callback(_log_task_exception)
