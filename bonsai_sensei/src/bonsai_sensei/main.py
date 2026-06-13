import logging
import os
import time
import traceback
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from functools import partial
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, PollAnswerHandler, filters

from bonsai_sensei.domain.services.sensei.advisor import create_advisor, AdvisorResponse
from bonsai_sensei.domain.services.sensei.session_manager import ChannelConfig
from bonsai_sensei.domain.services.sensei.session_manager import LAST_ACTIVITY_STATE_KEY
from bonsai_sensei.domain.services.cultivation.plan.refinement.factory import create_kiroku_group
from bonsai_sensei.memory.episodic_memory_service import EpisodicMemoryService, create_search_memory_func
from bonsai_sensei.domain.services.sensei.agents_factory import create_sensei_agent
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import create_tavily_searcher
from bonsai_sensei.domain.services.data_services import create_data_services
from bonsai_sensei.domain.services.human_input import (
    create_ask_confirmation,
    create_ask_human,
    create_ask_plan_review,
    create_ask_poll,
    create_ask_selection,
)
from bonsai_sensei.domain.services.mimamori.scheduler import create_mimamori_scheduler
from bonsai_sensei.domain.services.mimamori.mimamori_agent_runner import create_mimamori_agent_runner
from bonsai_sensei.domain.services.mimamori.context import build_bonsai_snapshots, build_reflection_context
from bonsai_sensei.domain.services.garden.caretaker.bonsai_events_tool import create_list_bonsai_events_tool
from bonsai_sensei.infrastructure.wiki_client import create_http_search_wiki_knowledge_tool, create_http_read_wiki_page_tool
from bonsai_sensei.domain.user_settings import UserSettings
from bonsai_sensei.logging_config import configure_logging
from bonsai_sensei.model_factory import (
    get_cloud_model_factory,
    get_cloud_orchestrator_model_factory,
    get_local_model_factory,
)
from bonsai_sensei.database.session import get_session, get_engine
from bonsai_sensei.observability import init_telemetry

from bonsai_sensei.telegram.messages.garden_messages import (
    build_create_bonsai_confirmation,
    build_create_bonsai_species_selection_question,
    build_delete_bonsai_confirmation,
    build_update_bonsai_confirmation,
    build_apply_fertilizer_confirmation,
    build_apply_phytosanitary_confirmation,
    build_record_transplant_confirmation,
    build_execute_planned_work_confirmation,
    build_execute_planned_work_selection_question,
    build_execute_planned_work_option_label,
    build_add_bonsai_photo_selection_question,
    build_add_bonsai_photo_confirmation,
    build_delete_bonsai_photo_selection_question,
    build_delete_bonsai_photo_confirmation,
    build_delete_bonsai_photo_option_label,
    build_create_pest_event_confirmation,
)
from bonsai_sensei.telegram.messages.planning_messages import (
    build_fertilizer_selection_question,
    build_fertilization_type_question,
    build_fertilization_type_options,
    build_period_question,
    build_phytosanitary_type_question,
    build_phytosanitary_type_options,
    build_phytosanitary_period_question,
    build_fertilizer_confirmation,
    build_phytosanitary_confirmation,
    build_transplant_confirmation,
    build_delete_confirmation,
    build_abandon_plan_confirmation,
    build_abandon_phytosanitary_plan_confirmation,
    build_abandon_development_plan_confirmation,
    build_bonsai_name_question,
    build_kiroku_work_selection_question,
    build_kiroku_work_option_label,
)
from bonsai_sensei.telegram.messages.storekeeper_messages import (
    build_create_fertilizer_confirmation,
    build_delete_fertilizer_confirmation,
    build_update_fertilizer_confirmation,
    build_create_phytosanitary_confirmation,
    build_delete_phytosanitary_confirmation,
    build_update_phytosanitary_confirmation,
)
from bonsai_sensei.telegram.messages.botanist_messages import (
    build_create_species_selection_question,
    build_create_species_confirmation,
    build_delete_species_confirmation,
    build_update_species_confirmation,
    build_refresh_species_wiki_confirmation,
    build_create_pest_confirmation,
    build_delete_pest_confirmation,
)
from bonsai_sensei.telegram.bot import TelegramBot
from bonsai_sensei.telegram.error_handler import error_handler
from bonsai_sensei.telegram.handle_confirmation_callback import handle_confirmation_callback
from bonsai_sensei.telegram.handle_plan_review_callback import handle_plan_review_callback
from bonsai_sensei.telegram.handle_selection_callback import handle_selection_callback
from bonsai_sensei.telegram.handle_poll_answer import handle_poll_answer
from bonsai_sensei.telegram.handle_user_message import handle_user_message
from bonsai_sensei.telegram.handle_user_photo import handle_user_photo
from bonsai_sensei.telegram.start import start
from bonsai_sensei.telegram.commands import (
    handle_mis_bonsais,
    handle_plan,
    handle_proximos,
    handle_fertilizantes,
    handle_fitosanitarios,
    handle_especies,
    handle_historial,
    handle_fin_de_semana,
    handle_plagas,
    handle_tiempo,
)
from bonsai_sensei.domain.services.cultivation.weather.weather import fetch_weather

from bonsai_sensei.api.species import router as species_router
from bonsai_sensei.api.bonsai import router as bonsai_router
from bonsai_sensei.api.fertilizers import router as fertilizers_router
from bonsai_sensei.api.phytosanitary import router as phytosanitary_router
from bonsai_sensei.api.advice import router as advice_router
from bonsai_sensei.api.weather import router as weather_router
from bonsai_sensei.api.telegram import router as telegram_router
from bonsai_sensei.api.user_settings import router as user_settings_router
from bonsai_sensei.api.planned_works import router as planned_works_router
from bonsai_sensei.api.fertilization_plans import router as fertilization_plans_router
from bonsai_sensei.api.phytosanitary_plans import router as phytosanitary_plans_router
from bonsai_sensei.api.development_plans import router as development_plans_router
from bonsai_sensei.api.mimamori import router as mimamori_router
from bonsai_sensei.api.pests import router as pests_router
from bonsai_sensei.api.health import router as health_router

KB_BASE_URL = os.getenv("KB_BASE_URL", "http://knowledge_base:8080")


async def _generic_exception_handler(request, exc):
    logging.exception("Unhandled exception while processing request")
    return JSONResponse(
        {
            "error": "backend proxy error",
            "details": traceback.format_exception(exc),
            "endpoint": str(request.url.path),
            "method": request.method,
        },
        status_code=500,
    )


def _save_telegram_chat_id(user_id: str, chat_id: str, save_user_settings):
    save_user_settings(UserSettings(user_id=user_id, telegram_chat_id=chat_id))


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_session_partial = partial(get_session, engine=get_engine())
    init_telemetry()

    services = create_data_services(get_session_partial)
    app.state.herbarium_service = services["herbarium"]
    app.state.garden_service = services["garden"]
    app.state.fertilizer_service = services["fertilizer"]
    app.state.phytosanitary_service = services["phytosanitary"]
    app.state.bonsai_history_service = services["bonsai_history"]
    app.state.user_settings_service = services["user_settings"]
    app.state.cultivation_plan_service = services["cultivation_plan"]
    app.state.fertilization_plan_service = services["fertilization_plan"]
    app.state.phytosanitary_plan_service = services["phytosanitary_plan"]
    app.state.development_plan_service = services["development_plan"]
    app.state.bonsai_photo_service = services["bonsai_photo"]
    app.state.pest_service = services["pest"]
    app.state.pending_human_responses = {}
    app.state.pending_confirmation_cleanups = {}
    app.state.active_tasks = {}
    app.state.background_tasks: set = set()
    app.state.pending_photos = {}
    app.state.poll_id_to_user_id = {}

    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    model_factory = get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    model = model_factory()
    orchestrator_model = get_cloud_orchestrator_model_factory()() if provider == "cloud" else None

    bot_instance = TelegramBot(error_handler=error_handler)

    def _resolve_chat_id(user_id: str) -> str | None:
        if user_id is not None and user_id.lstrip("-").isdigit():
            return user_id
        return None

    async def send_confirmation_func(user_id: str, question: str, confirmation_id: str):
        chat_id = _resolve_chat_id(user_id)
        if chat_id:
            await bot_instance.send_confirmation_message(chat_id=chat_id, text=question, confirmation_id=confirmation_id)

    async def send_message_func(user_id: str, text: str):
        chat_id = _resolve_chat_id(user_id)
        if chat_id:
            await bot_instance.send_message(chat_id=chat_id, text=text)

    async def send_selection_func(user_id: str, question: str, options: list, selection_id: str):
        chat_id = _resolve_chat_id(user_id)
        if chat_id:
            await bot_instance.send_selection_message(chat_id=chat_id, question=question, options=options, selection_id=selection_id)

    async def send_plan_review_func(user_id: str, proposal: str, review_id: str):
        chat_id = _resolve_chat_id(user_id)
        if chat_id:
            await bot_instance.send_plan_review_message(chat_id=chat_id, text=proposal, review_id=review_id)

    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    async def send_photo_selection_func(user_id: str, question: str, options: list[str], photo_paths: list[str], selection_id: str):
        chat_id = _resolve_chat_id(user_id)
        if not chat_id:
            return
        from bonsai_sensei.telegram.photo_thumbnail import generate_labeled_thumbnail
        thumbnail_paths = []
        try:
            for option, photo_path in zip(options, photo_paths):
                full_path = str(photos_root / photo_path)
                label = option.replace("Foto del ", "📅 ")
                thumbnail_paths.append(generate_labeled_thumbnail(full_path, label))
            await bot_instance.send_selection_with_photos(
                chat_id=chat_id,
                question=question,
                options=options,
                photo_file_paths=thumbnail_paths,
                selection_id=selection_id,
            )
        except Exception:
            logging.exception("Photo thumbnail generation failed, falling back to text selection")
            await bot_instance.send_selection_message(
                chat_id=chat_id,
                question=question,
                options=options,
                selection_id=selection_id,
            )
        finally:
            for tmp_path in thumbnail_paths:
                Path(tmp_path).unlink(missing_ok=True)

    ask_confirmation_func = create_ask_confirmation(send_confirmation_func, app.state.pending_human_responses)
    ask_human_func = create_ask_human(send_message_func, app.state.pending_human_responses)
    ask_selection_func = create_ask_selection(send_selection_func, app.state.pending_human_responses, send_photo_selection_func=send_photo_selection_func)
    ask_plan_review_func = create_ask_plan_review(send_plan_review_func, app.state.pending_human_responses)

    async def send_poll_func(user_id: str, question: str, options: list[str]) -> str:
        chat_id = _resolve_chat_id(user_id)
        if not chat_id:
            return None
        return await bot_instance.send_poll_message(chat_id=chat_id, question=question, options=options)

    ask_poll_func = create_ask_poll(send_poll_func, app.state.pending_human_responses, app.state.poll_id_to_user_id, send_message_func=send_message_func)

    tavily_api_key = os.getenv("TAVILY_API_KEY")
    tavily_base_url = os.getenv("TAVILY_API_BASE")
    tavily_searcher = create_tavily_searcher(tavily_api_key, tavily_base_url) if tavily_api_key else None

    episodic_memory_url = os.getenv("EPISODIC_MEMORY_URL", "")
    memory_service = EpisodicMemoryService(episodic_memory_url) if episodic_memory_url else None
    search_memory_func = create_search_memory_func(episodic_memory_url) if episodic_memory_url else None

    sensei_agent = create_sensei_agent(
        model=model,
        session_factory=get_session_partial,
        orchestrator_model=orchestrator_model,
        pending_photos=app.state.pending_photos,
        ask_confirmation=ask_confirmation_func,
        ask_human=ask_human_func,
        ask_selection=ask_selection_func,
        ask_plan_review=ask_plan_review_func,
        ask_poll=ask_poll_func,
        searcher=tavily_searcher,
        register_background_task=lambda task: app.state.background_tasks.add(task),
        kb_base_url=KB_BASE_URL,
        search_memory_func=search_memory_func,
        cultivation_messages={
            "build_fertilizer_selection_question": build_fertilizer_selection_question,
            "build_fertilization_type_question": build_fertilization_type_question,
            "build_fertilization_type_options": build_fertilization_type_options,
            "build_period_question": build_period_question,
            "build_phytosanitary_type_question": build_phytosanitary_type_question,
            "build_phytosanitary_type_options": build_phytosanitary_type_options,
            "build_phytosanitary_period_question": build_phytosanitary_period_question,
            "build_fertilizer_confirmation": build_fertilizer_confirmation,
            "build_phytosanitary_confirmation": build_phytosanitary_confirmation,
            "build_transplant_confirmation": build_transplant_confirmation,
            "build_delete_confirmation": build_delete_confirmation,
            "build_abandon_plan_confirmation": build_abandon_plan_confirmation,
            "build_abandon_phytosanitary_plan_confirmation": build_abandon_phytosanitary_plan_confirmation,
            "build_abandon_development_plan_confirmation": build_abandon_development_plan_confirmation,
            "build_bonsai_name_question": build_bonsai_name_question,
            "build_kiroku_work_selection_question": build_kiroku_work_selection_question,
            "build_kiroku_work_option_label": build_kiroku_work_option_label,
        },
        garden_messages={
            "build_create_bonsai_confirmation": build_create_bonsai_confirmation,
            "build_create_bonsai_species_selection_question": build_create_bonsai_species_selection_question,
            "build_delete_bonsai_confirmation": build_delete_bonsai_confirmation,
            "build_update_bonsai_confirmation": build_update_bonsai_confirmation,
            "build_apply_fertilizer_confirmation": build_apply_fertilizer_confirmation,
            "build_apply_phytosanitary_confirmation": build_apply_phytosanitary_confirmation,
            "build_record_transplant_confirmation": build_record_transplant_confirmation,
            "build_execute_planned_work_confirmation": build_execute_planned_work_confirmation,
            "build_execute_planned_work_selection_question": build_execute_planned_work_selection_question,
            "build_execute_planned_work_option_label": build_execute_planned_work_option_label,
            "build_create_pest_event_confirmation": build_create_pest_event_confirmation,
            "build_add_bonsai_photo_selection_question": build_add_bonsai_photo_selection_question,
            "build_add_bonsai_photo_confirmation": build_add_bonsai_photo_confirmation,
            "build_delete_bonsai_photo_selection_question": build_delete_bonsai_photo_selection_question,
            "build_delete_bonsai_photo_confirmation": build_delete_bonsai_photo_confirmation,
            "build_delete_bonsai_photo_option_label": build_delete_bonsai_photo_option_label,
        },
        storekeeper_messages={
            "build_create_fertilizer_confirmation": build_create_fertilizer_confirmation,
            "build_delete_fertilizer_confirmation": build_delete_fertilizer_confirmation,
            "build_update_fertilizer_confirmation": build_update_fertilizer_confirmation,
            "build_create_phytosanitary_confirmation": build_create_phytosanitary_confirmation,
            "build_delete_phytosanitary_confirmation": build_delete_phytosanitary_confirmation,
            "build_update_phytosanitary_confirmation": build_update_phytosanitary_confirmation,
        },
        botanist_messages={
            "build_create_species_selection_question": build_create_species_selection_question,
            "build_create_species_confirmation": build_create_species_confirmation,
            "build_delete_species_confirmation": build_delete_species_confirmation,
            "build_update_species_confirmation": build_update_species_confirmation,
            "build_refresh_species_wiki_confirmation": build_refresh_species_wiki_confirmation,
            "build_create_pest_confirmation": build_create_pest_confirmation,
            "build_delete_pest_confirmation": build_delete_pest_confirmation,
        },
    )

    kiroku_agent = create_kiroku_group(
        model=model,
        session_factory=get_session_partial,
        ask_human=ask_human_func,
        ask_selection=ask_selection_func,
        build_bonsai_name_question=build_bonsai_name_question,
        build_work_selection_question=build_kiroku_work_selection_question,
        build_work_option_label=build_kiroku_work_option_label,
        pending_photos=app.state.pending_photos,
        orchestrator_model=orchestrator_model,
        search_memory_func=search_memory_func,
    )

    get_user_settings_func = services["user_settings"]["get_user_settings"]

    def build_sensei_context_state(user_id: str) -> dict:
        user_settings = get_user_settings_func(user_id)
        user_location = user_settings.location if user_settings and user_settings.location else ""
        today = date.today()
        days_until_saturday = (5 - today.weekday()) % 7 or 7
        next_saturday = (today + timedelta(days=days_until_saturday)).isoformat()
        return {
            "current_date": today.isoformat(),
            "next_saturday": next_saturday,
            "user_location": user_location,
            "photos_to_display": [],
            "photos_for_analysis_taken_on": [],
            LAST_ACTIVITY_STATE_KEY: datetime.now(timezone.utc).isoformat(),
        }

    app.state.advisor, app.state.reset_session = create_advisor(
        default_agent=sensei_agent,
        channels=[
            ChannelConfig(
                name="kiroku",
                agent=kiroku_agent,
                session_id_for=lambda uid: f"{uid}:kiroku",
                state_init_prefix="kiroku_",
            ),
        ],
        progress_messages={
            "command_pipeline": "🗺️ Elaborando un plan de acción...",
            "gardener": "🌱 Gestionando la colección de bonsáis...",
            "kantei": "🔍 Analizando la foto...",
            "botanist": "🌿 Consultando el herbario de especies...",
            "kikaru": "📅 Planificando trabajos de cultivo...",
            "kiroku": "📝 Documentando el trabajo...",
            "weather_advisor": "🌤️ Consultando el pronóstico meteorológico...",
            "storekeeper": "📦 Consultando el catálogo de insumos...",
            "recommend_fertilizer": "🧪 Seleccionando fertilizante...",
            "recommend_phytosanitary": "🛡️ Seleccionando producto fitosanitario...",
        },
        context_state_builder=build_sensei_context_state,
        memory_service=memory_service,
    )

    save_telegram_chat_id_func = partial(
        _save_telegram_chat_id,
        save_user_settings=services["user_settings"]["save_user_settings"],
    )
    users_awaiting_location: set = set()
    message_handler = partial(
        handle_user_message,
        message_processor=app.state.advisor,
        save_telegram_chat_id_func=save_telegram_chat_id_func,
        get_user_settings_func=services["user_settings"]["get_user_settings"],
        ask_confirmation=ask_confirmation_func,
        save_user_settings_func=services["user_settings"]["save_user_settings"],
        users_awaiting_location=users_awaiting_location,
        pending_human_responses=app.state.pending_human_responses,
        pending_confirmation_cleanups=app.state.pending_confirmation_cleanups,
    )
    photo_handler = partial(
        handle_user_photo,
        message_processor=app.state.advisor,
        save_telegram_chat_id_func=save_telegram_chat_id_func,
        pending_confirmation_cleanups=app.state.pending_confirmation_cleanups,
        pending_photos=app.state.pending_photos,
    )
    confirmation_handler = partial(
        handle_confirmation_callback,
        pending_human_responses=app.state.pending_human_responses,
        pending_confirmation_cleanups=app.state.pending_confirmation_cleanups,
        send_cancel_reason_prompt=bot_instance.send_force_reply_message,
    )
    plan_review_handler = partial(
        handle_plan_review_callback,
        pending_human_responses=app.state.pending_human_responses,
        pending_confirmation_cleanups=app.state.pending_confirmation_cleanups,
    )
    selection_handler = partial(
        handle_selection_callback,
        pending_human_responses=app.state.pending_human_responses,
        pending_confirmation_cleanups=app.state.pending_confirmation_cleanups,
        send_none_reason_prompt=bot_instance.send_force_reply_message,
    )
    poll_answer_handler = partial(
        handle_poll_answer,
        pending_human_responses=app.state.pending_human_responses,
        poll_id_to_user_id=app.state.poll_id_to_user_id,
        send_free_text_prompt=bot_instance.send_force_reply_message,
    )

    mis_bonsais_handler = partial(
        handle_mis_bonsais,
        list_bonsai_func=services["garden"]["list_bonsai"],
        list_species_func=services["herbarium"]["list_species"],
    )
    plan_handler = partial(
        handle_plan,
        get_bonsai_by_name_func=services["garden"]["get_bonsai_by_name"],
        list_planned_works_func=services["cultivation_plan"]["list_planned_works"],
    )
    proximos_handler = partial(
        handle_proximos,
        list_planned_works_in_date_range_func=services["cultivation_plan"]["list_planned_works_in_date_range"],
        list_bonsai_func=services["garden"]["list_bonsai"],
    )
    fertilizantes_handler = partial(
        handle_fertilizantes,
        list_fertilizers_func=services["fertilizer"]["list_fertilizers"],
    )
    fitosanitarios_handler = partial(
        handle_fitosanitarios,
        list_phytosanitary_func=services["phytosanitary"]["list_phytosanitary"],
    )
    especies_handler = partial(
        handle_especies,
        list_species_func=services["herbarium"]["list_species"],
    )
    historial_handler = partial(
        handle_historial,
        get_bonsai_by_name_func=services["garden"]["get_bonsai_by_name"],
        list_bonsai_events_func=services["bonsai_history"]["list_bonsai_events"],
    )
    fin_de_semana_handler = partial(
        handle_fin_de_semana,
        list_planned_works_in_date_range_func=services["cultivation_plan"]["list_planned_works_in_date_range"],
        list_bonsai_func=services["garden"]["list_bonsai"],
    )
    plagas_handler = partial(
        handle_plagas,
        list_pests_func=services["pest"]["list_pests"],
    )
    tiempo_handler = partial(
        handle_tiempo,
        get_user_settings_func=services["user_settings"]["get_user_settings"],
        get_weather_func=fetch_weather,
    )
    user_bot_handlers = [
        CommandHandler("start", start),
        CommandHandler("mis_bonsais", mis_bonsais_handler),
        CommandHandler("plan", plan_handler),
        CommandHandler("proximos", proximos_handler),
        CommandHandler("fertilizantes", fertilizantes_handler),
        CommandHandler("fitosanitarios", fitosanitarios_handler),
        CommandHandler("especies", especies_handler),
        CommandHandler("historial", historial_handler),
        CommandHandler("fin_de_semana", fin_de_semana_handler),
        CommandHandler("plagas", plagas_handler),
        CommandHandler("tiempo", tiempo_handler),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
        MessageHandler(filters.PHOTO, photo_handler),
        CallbackQueryHandler(confirmation_handler, pattern=r"^confirm:(accept|cancel):.+$"),
        CallbackQueryHandler(plan_review_handler, pattern=r"^plan_review:.+:(confirm|correct|cancel)$"),
        CallbackQueryHandler(selection_handler, pattern=r"^selection:.+:(\d+|none)$"),
        PollAnswerHandler(poll_answer_handler),
    ]
    if bot_instance.application:
        for handler in user_bot_handlers:
            bot_instance.application.add_handler(handler)

    app.state.bot = bot_instance
    await bot_instance.initialize()

    list_bonsai_events_tool = create_list_bonsai_events_tool(
        get_bonsai_by_name_func=services["garden"]["get_bonsai_by_name"],
        list_bonsai_events_func=services["bonsai_history"]["list_bonsai_events"],
    )
    app.state.mimamori_runner = create_mimamori_agent_runner(
        model=orchestrator_model or model,
        search_wiki_knowledge=create_http_search_wiki_knowledge_tool(KB_BASE_URL) if KB_BASE_URL else None,
        read_wiki_page=create_http_read_wiki_page_tool(KB_BASE_URL) if KB_BASE_URL else None,
        list_bonsai_events=list_bonsai_events_tool,
        memory_service=memory_service,
    )
    app.state.mimamori_build_bonsai_snapshots = partial(
        build_bonsai_snapshots,
        list_bonsai_events_func=services["bonsai_history"]["list_bonsai_events"],
        get_active_development_plan_func=services["development_plan"]["get_active_development_plan"],
        get_active_fertilization_plan_func=services["fertilization_plan"]["get_active_fertilization_plan"],
        get_recent_unlinked_pest_events_func=services["bonsai_history"]["get_recent_unlinked_pest_events"],
        get_recently_abandoned_fertilization_plans_func=services["fertilization_plan"]["get_recently_abandoned_fertilization_plans"],
        get_recently_abandoned_development_plans_func=services["development_plan"]["get_recently_abandoned_development_plans"],
    )
    app.state.mimamori_build_reflection_context = partial(
        build_reflection_context,
        fetch_weather_func=fetch_weather,
    )

    mimamori_scheduler = create_mimamori_scheduler(
        run_mimamori_reflection=app.state.mimamori_runner,
        build_bonsai_snapshots_func=app.state.mimamori_build_bonsai_snapshots,
        build_reflection_context_func=app.state.mimamori_build_reflection_context,
        list_all_user_settings_func=services["user_settings"]["list_all_user_settings"],
        list_bonsai_func=services["garden"]["list_bonsai"],
        list_species_func=services["herbarium"]["list_species"],
        list_planned_works_in_date_range_func=services["cultivation_plan"]["list_planned_works_in_date_range"],
        send_telegram_message_func=app.state.bot.send_message,
        search_memory_func=search_memory_func,
    )

    yield

    mimamori_scheduler.shutdown()
    await bot_instance.shutdown()


configure_logging()

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
app.add_exception_handler(Exception, _generic_exception_handler)


app.include_router(health_router, tags=["health"])
app.include_router(species_router, prefix="/api", tags=["species"])
app.include_router(bonsai_router, prefix="/api", tags=["bonsai"])
app.include_router(fertilizers_router, prefix="/api", tags=["fertilizers"])
app.include_router(phytosanitary_router, prefix="/api", tags=["phytosanitary"])
app.include_router(advice_router, prefix="/api", tags=["advice"])
app.include_router(weather_router, prefix="/api", tags=["weather"])
app.include_router(user_settings_router, prefix="/api", tags=["user_settings"])
app.include_router(planned_works_router, prefix="/api", tags=["planned_works"])
app.include_router(fertilization_plans_router, prefix="/api", tags=["fertilization_plans"])
app.include_router(phytosanitary_plans_router, prefix="/api", tags=["phytosanitary_plans"])
app.include_router(development_plans_router, prefix="/api", tags=["development_plans"])
app.include_router(mimamori_router, prefix="/api", tags=["mimamori"])
app.include_router(pests_router, prefix="/api", tags=["pests"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
