from datetime import date, timedelta

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bonsai_sensei.logging_config import get_logger
from bonsai_sensei.telegram.messages.commands_messages import (
    build_bonsai_history,
    build_bonsai_list,
    build_fertilizer_list,
    build_no_location_message,
    build_pest_list,
    build_phytosanitary_list,
    build_planned_works_list,
    build_species_list,
    build_upcoming_works_list,
    build_weather_message,
    build_weekend_works_list,
)

logger = get_logger(__name__)

_UPCOMING_DAYS = 14


async def handle_mis_bonsais(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_bonsai_func=None,
    list_species_func=None,
):
    user_id = str(update.effective_user.id)
    bonsais = list_bonsai_func(user_id=user_id)
    species_list = list_species_func()
    species_id_to_name = {species.id: species.name for species in species_list}
    text = build_bonsai_list(bonsais, species_id_to_name)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_plan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    get_bonsai_by_name_func=None,
    list_planned_works_func=None,
):
    if not context.args:
        await update.message.reply_text("Uso: /plan <nombre_bonsai>")
        return
    user_id = str(update.effective_user.id)
    bonsai_name = " ".join(context.args)
    bonsai = get_bonsai_by_name_func(bonsai_name, user_id=user_id)
    if not bonsai:
        await update.message.reply_text(f"No encontré ningún bonsái llamado '{bonsai_name}'.")
        return
    works = list_planned_works_func(bonsai.id)
    text = build_planned_works_list(bonsai.name, works)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_proximos(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_planned_works_in_date_range_func=None,
    list_bonsai_func=None,
):
    user_id = str(update.effective_user.id)
    today = date.today()
    works = list_planned_works_in_date_range_func(today, today + timedelta(days=_UPCOMING_DAYS))
    bonsais = list_bonsai_func(user_id=user_id)
    bonsai_id_to_name = {bonsai.id: bonsai.name for bonsai in bonsais}
    text = build_upcoming_works_list(works, bonsai_id_to_name)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_fertilizantes(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_fertilizers_func=None,
):
    user_id = str(update.effective_user.id)
    fertilizers = list_fertilizers_func(user_id=user_id)
    text = build_fertilizer_list(fertilizers)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_fitosanitarios(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_phytosanitary_func=None,
):
    user_id = str(update.effective_user.id)
    phytosanitaries = list_phytosanitary_func(user_id=user_id)
    text = build_phytosanitary_list(phytosanitaries)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_especies(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_species_func=None,
):
    species_list = list_species_func()
    text = build_species_list(species_list)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_historial(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    get_bonsai_by_name_func=None,
    list_bonsai_events_func=None,
):
    if not context.args:
        await update.message.reply_text("Uso: /historial <nombre_bonsai>")
        return
    user_id = str(update.effective_user.id)
    bonsai_name = " ".join(context.args)
    bonsai = get_bonsai_by_name_func(bonsai_name, user_id=user_id)
    if not bonsai:
        await update.message.reply_text(f"No encontré ningún bonsái llamado '{bonsai_name}'.")
        return
    events = list_bonsai_events_func(bonsai.id)
    text = build_bonsai_history(bonsai.name, events)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_fin_de_semana(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_planned_works_in_date_range_func=None,
    list_bonsai_func=None,
):
    user_id = str(update.effective_user.id)
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7 or 7
    saturday = today + timedelta(days=days_until_saturday)
    sunday = saturday + timedelta(days=1)
    works = list_planned_works_in_date_range_func(saturday, sunday)
    bonsais = list_bonsai_func(user_id=user_id)
    bonsai_id_to_name = {bonsai.id: bonsai.name for bonsai in bonsais}
    text = build_weekend_works_list(saturday, sunday, works, bonsai_id_to_name)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_plagas(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    list_pests_func=None,
):
    pests = list_pests_func()
    text = build_pest_list(pests)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def handle_tiempo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    get_user_settings_func=None,
    get_weather_func=None,
):
    location = " ".join(context.args) if context.args else None
    if not location:
        user_id = str(update.effective_user.id)
        user_settings = get_user_settings_func(user_id)
        location = user_settings.location if user_settings else None
    if not location:
        await update.message.reply_text(build_no_location_message())
        return
    weather_result = await get_weather_func(location)
    text = build_weather_message(weather_result)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
