import time
from typing import Callable

from opentelemetry import metrics
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, TimedOut
from telegram.ext import ContextTypes

from bonsai_sensei.domain.services.advisor import AdvisorResponse
from bonsai_sensei.domain.user_settings import UserSettings
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_meter = metrics.get_meter(__name__)
_message_counter = _meter.create_counter(
    "telegram.message.count",
    description="Number of Telegram messages processed",
)
_message_latency = _meter.create_histogram(
    "telegram.message.latency",
    unit="ms",
    description="End-to-end Telegram message processing latency in milliseconds",
)

LOCATION_REQUEST_MESSAGE = (
    "¡Hola! Para enviarte alertas meteorológicas diarias y ayudarte a proteger tus bonsáis, "
    "¿cuál es tu ubicación? Puedes indicar ciudad, código postal o coordenadas."
)


async def handle_user_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_processor=None,
    save_telegram_chat_id_func=None,
    get_user_settings_func=None,
    ask_confirmation: Callable | None = None,
    save_user_settings_func=None,
    users_awaiting_location: set | None = None,
    pending_human_responses: dict | None = None,
):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    logger.info(f"Received message from {user_id}: {update.message.text}")

    if save_telegram_chat_id_func:
        save_telegram_chat_id_func(user_id, chat_id)

    if pending_human_responses and user_id in pending_human_responses:
        pending_human_responses[user_id]["response"] = update.message.text
        pending_human_responses[user_id]["event"].set()
        return

    if _is_location_response(user_id, users_awaiting_location):
        users_awaiting_location.discard(user_id)
        await _confirm_and_save_location(
            update, user_id, update.message.text, ask_confirmation, save_user_settings_func
        )
        return

    if _needs_location(user_id, get_user_settings_func, users_awaiting_location):
        users_awaiting_location.add(user_id)
        await update.message.reply_text(LOCATION_REQUEST_MESSAGE)
        return

    if not message_processor:
        logger.error("No message processor configured for message handler")
        await update.message.reply_text("Error interno: No puedo procesar tu mensaje.")
        return

    start_time = time.monotonic()
    progress_message = await update.message.reply_text("⏳ Procesando...")
    last_progress_text = "⏳ Procesando..."

    async def update_progress(text: str) -> None:
        nonlocal last_progress_text
        if text == last_progress_text:
            return
        last_progress_text = text
        try:
            await progress_message.edit_text(text)
        except Exception:
            pass

    try:
        response: AdvisorResponse = await message_processor(
            update.message.text, user_id=user_id, progress_callback=update_progress
        )
    finally:
        try:
            await progress_message.delete()
        except Exception:
            pass

    await _reply_with_html(update, response.text)

    latency_ms = (time.monotonic() - start_time) * 1000
    _message_counter.add(1, {"user.id": user_id})
    _message_latency.record(latency_ms, {"user.id": user_id})


async def _confirm_and_save_location(
    update: Update,
    user_id: str,
    location: str,
    ask_confirmation: Callable | None,
    save_user_settings_func,
) -> None:
    if not ask_confirmation or not save_user_settings_func:
        return
    confirmed = await ask_confirmation(
        f"¿Confirmas que tu ubicación es: {location}?",
        user_id=user_id,
    )
    if confirmed:
        save_user_settings_func(UserSettings(user_id=user_id, location=location))
        await update.message.reply_text("Ubicación guardada correctamente.")
    else:
        await update.message.reply_text("Ubicación cancelada.")


async def _reply_with_html(update: Update, text: str) -> None:
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except (BadRequest, TimedOut):
        logger.warning("Failed to send message with HTML, falling back to plain text")
        await update.message.reply_text(text)


def _needs_location(user_id: str, get_user_settings_func, users_awaiting_location: set | None) -> bool:
    if get_user_settings_func is None or users_awaiting_location is None:
        return False
    if user_id in users_awaiting_location:
        return False
    user_settings = get_user_settings_func(user_id)
    return user_settings is None or not user_settings.location


def _is_location_response(user_id: str, users_awaiting_location: set | None) -> bool:
    return users_awaiting_location is not None and user_id in users_awaiting_location
