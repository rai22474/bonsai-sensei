import io

from PIL import Image
from google.genai import types
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TimedOut
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.telegram.messages._formatting import random_processing_message

logger = get_logger(__name__)


async def handle_user_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_processor=None,
    save_telegram_chat_id_func=None,
    pending_confirmation_cleanups: dict | None = None,
    pending_photos: dict | None = None,
):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    logger.info(f"Received photo from {user_id}")

    if save_telegram_chat_id_func:
        save_telegram_chat_id_func(user_id, chat_id)

    if not message_processor:
        logger.error("No message processor configured for photo handler")
        return

    webp_bytes = await _download_as_webp(update, context)

    if pending_photos is not None:
        pending_photos[user_id] = webp_bytes

    progress_message = await update.message.reply_text(random_processing_message())

    try:
        response = await message_processor(_build_photo_message(webp_bytes), user_id=user_id)
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


async def _download_as_webp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bytes:
    photo = update.message.photo[-1]
    telegram_file = await context.bot.get_file(photo.file_id)
    raw_bytes = await telegram_file.download_as_bytearray()
    buffer = io.BytesIO()
    Image.open(io.BytesIO(raw_bytes)).save(buffer, format="WEBP", quality=85)
    return buffer.getvalue()


def _build_photo_message(webp_bytes: bytes) -> types.Content:
    return types.Content(
        role="user",
        parts=[
            types.Part(inline_data=types.Blob(mime_type="image/webp", data=webp_bytes)),
            types.Part(text="El usuario ha enviado una foto."),
        ],
    )


async def _reply_with_html(update: Update, text: str) -> None:
    if not text or not text.strip():
        logger.warning("Empty response text, skipping reply")
        return
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except (BadRequest, TimedOut):
        logger.warning("Failed to send photo response with HTML, falling back to plain text")
        await update.message.reply_text(text)
