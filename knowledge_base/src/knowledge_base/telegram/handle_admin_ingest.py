import asyncio
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from knowledge_base.ingestion.transcript_loader import extract_video_id
from knowledge_base.logging_config import get_logger

logger = get_logger(__name__)


async def handle_admin_ingest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    ingest_transcript: Callable,
    fetch_channel_slug: Callable,
    text_override: str | None = None,
) -> None:
    text = (text_override or update.message.text or "").strip()
    parts = text.split()
    raw_url = parts[0]
    channel = parts[1] if len(parts) > 1 else None

    try:
        video_id = extract_video_id(raw_url)
        url = f"https://www.youtube.com/watch?v={video_id}"
    except ValueError:
        await update.message.reply_text(f"❌ No puedo extraer el video ID de: {raw_url}")
        return

    if channel is None:
        channel = fetch_channel_slug(video_id)
        logger.info("Auto-resolved channel slug: video_id=%s channel=%s", video_id, channel)

    await update.message.reply_text(f"⚙️ Ingestando {video_id} (canal: {channel})...")
    logger.info("Admin triggered ingestion: video_id=%s channel=%s", video_id, channel)

    async def on_step(message: str) -> None:
        try:
            await update.message.reply_text(message)
        except Exception:
            pass

    async def run_and_catch():
        try:
            await ingest_transcript(url, channel, on_step=on_step)
        except Exception:
            logger.exception("Ingestion failed for %s", video_id)
            await update.message.reply_text(f"❌ Error durante la ingestión de {video_id}.")

    asyncio.create_task(run_and_catch())
