import io
import os
import uuid
from pathlib import Path

from PIL import Image
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TimedOut
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.telegram.messages._formatting import random_processing_message

logger = get_logger(__name__)

PHOTOS_PATH = os.getenv("PHOTOS_PATH", "./photos")


async def handle_user_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_processor=None,
    save_telegram_chat_id_func=None,
    pending_human_responses: dict | None = None,
    pending_confirmation_cleanups: dict | None = None,
):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    logger.info(f"Received photo from {user_id}")

    if save_telegram_chat_id_func:
        save_telegram_chat_id_func(user_id, chat_id)

    if not message_processor:
        logger.error("No message processor configured for photo handler")
        return

    photo = update.message.photo[-1]
    telegram_file = await context.bot.get_file(photo.file_id)

    photos_dir = Path(PHOTOS_PATH)
    photos_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4().hex}.webp"
    file_path = photos_dir / file_name

    raw_bytes = await telegram_file.download_as_bytearray()
    image = Image.open(io.BytesIO(raw_bytes))
    image.save(file_path, format="WEBP", quality=85)

    progress_message = await update.message.reply_text(random_processing_message())

    advisor_message = f"[FOTO RECIBIDA: {file_name}] El usuario ha enviado una foto."

    try:
        response = await message_processor(advisor_message, user_id=user_id)
    finally:
        try:
            await progress_message.delete()
        except Exception:
            pass
        for cleanup in (pending_confirmation_cleanups or {}).pop(user_id, []):
            try:
                await cleanup()
            except Exception:
                pass

    logger.info(f"Photo response for {user_id}: {repr(response.text[:100] if response.text else '')}")
    await _reply_with_html(update, response.text)


async def _reply_with_html(update: Update, text: str) -> None:
    if not text or not text.strip():
        logger.warning("Empty response text, skipping reply")
        return
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except (BadRequest, TimedOut):
        logger.warning("Failed to send photo response with HTML, falling back to plain text")
        await update.message.reply_text(text)
