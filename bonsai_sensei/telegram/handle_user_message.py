import uuid
from functools import partial

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest, TimedOut
from telegram.ext import ContextTypes

from bonsai_sensei.domain.confirmation import Confirmation
from bonsai_sensei.domain.confirmation_store import ConfirmationStore
from bonsai_sensei.domain.services.advisor import AdvisorResponse
from bonsai_sensei.domain.user_settings import UserSettings
from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

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
    confirmation_store: ConfirmationStore | None = None,
    save_user_settings_func=None,
    users_awaiting_location: set | None = None,
):
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    logger.info(f"Received message from {user_id}: {update.message.text}")

    if save_telegram_chat_id_func:
        save_telegram_chat_id_func(user_id, chat_id)

    if _is_location_response(user_id, users_awaiting_location):
        users_awaiting_location.discard(user_id)
        await _register_location_confirmation(
            update, user_id, update.message.text, confirmation_store, save_user_settings_func
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

    response: AdvisorResponse = await message_processor(update.message.text, user_id=user_id)

    await _reply_with_html(update, response.text)

    for pending in response.pending_confirmations:
        await update.message.reply_text(
            pending.summary,
            reply_markup=_create_confirmation_keyboard(pending.id),
        )


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


async def _register_location_confirmation(
    update: Update,
    user_id: str,
    location: str,
    confirmation_store: ConfirmationStore | None,
    save_user_settings_func,
):
    if not confirmation_store or not save_user_settings_func:
        return

    confirmation = Confirmation(
        id=uuid.uuid4().hex,
        user_id=user_id,
        summary=f"Guardar ubicación: {location}",
        executor=partial(
            save_user_settings_func,
            UserSettings(user_id=user_id, location=location),
        ),
        deduplication_key=f"save_location:{user_id}",
    )
    confirmation_store.set_pending(user_id, confirmation)

    await update.message.reply_text(
        f"¿Confirmas que tu ubicación es: {location}?",
        reply_markup=_create_confirmation_keyboard(confirmation.id),
    )


def _create_confirmation_keyboard(confirmation_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Aceptar", callback_data=f"confirm:accept:{confirmation_id}"),
                InlineKeyboardButton("Cancelar", callback_data=f"confirm:cancel:{confirmation_id}"),
            ]
        ]
    )
