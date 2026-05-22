import logging
import os
import traceback
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, PollAnswerHandler, filters

from bonsai_sensei.domain.services.advisor import create_advisor
from bonsai_sensei.memory.mem0_memory_service import Mem0MemoryService, create_mem0_client
from bonsai_sensei.domain.services.agents_factory import create_sensei_agent
from bonsai_sensei.domain.services.cultivation.species.tavily_searcher import create_tavily_searcher
from bonsai_sensei.domain.services.data_services import create_data_services
from bonsai_sensei.domain.services.human_input import (
    create_ask_confirmation,
    create_ask_human,
    create_ask_plan_review,
    create_ask_poll,
    create_ask_selection,
)
from bonsai_sensei.domain.services.cultivation.weather.weather_alert_scheduler import create_weather_alert_scheduler
from bonsai_sensei.domain.services.cultivation.plan.weekend_plan_scheduler import create_weekend_plan_scheduler
from bonsai_sensei.domain.user_settings import UserSettings
from bonsai_sensei.knowledge_base.ingestion.factory import create_ingestion_pipeline
from bonsai_sensei.knowledge_base.keeper.runner import create_wiki_keeper
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
from bonsai_sensei.api.weekend_plan_reminder import router as weekend_plan_reminder_router
from bonsai_sensei.api.wiki import router as wiki_router
from bonsai_sensei.api.transcripts import router as transcripts_router
from bonsai_sensei.api.pests import router as pests_router


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
    app.state.bonsai_photo_service = services["bonsai_photo"]
    app.state.pest_service = services["pest"]
    app.state.pending_human_responses = {}
    app.state.pending_confirmation_cleanups = {}
    app.state.active_tasks = {}
    app.state.pending_photos = {}
    app.state.poll_id_to_user_id = {}

    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    model_factory = get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    model = model_factory()
    orchestrator_model = get_cloud_orchestrator_model_factory()() if provider == "cloud" else None

    bot_instance = TelegramBot(error_handler=error_handler)

    async def send_confirmation_func(user_id: str, question: str, confirmation_id: str):
        await bot_instance.send_confirmation_message(chat_id=user_id, text=question, confirmation_id=confirmation_id)

    async def send_message_func(user_id: str, text: str):
        await bot_instance.send_message(chat_id=user_id, text=text)

    async def send_selection_func(user_id: str, question: str, options: list, selection_id: str):
        await bot_instance.send_selection_message(chat_id=user_id, question=question, options=options, selection_id=selection_id)

    async def send_plan_review_func(user_id: str, proposal: str, review_id: str):
        await bot_instance.send_plan_review_message(chat_id=user_id, text=proposal, review_id=review_id)

    photos_root = Path(os.getenv("PHOTOS_PATH", "./photos"))

    async def send_photo_selection_func(user_id: str, question: str, options: list[str], photo_paths: list[str], selection_id: str):
        from bonsai_sensei.telegram.photo_thumbnail import generate_labeled_thumbnail
        thumbnail_paths = []
        try:
            for option, photo_path in zip(options, photo_paths):
                full_path = str(photos_root / photo_path)
                label = option.replace("Foto del ", "📅 ")
                thumbnail_paths.append(generate_labeled_thumbnail(full_path, label))
            await bot_instance.send_selection_with_photos(
                chat_id=user_id,
                question=question,
                options=options,
                photo_file_paths=thumbnail_paths,
                selection_id=selection_id,
            )
        except Exception:
            logging.exception("Photo thumbnail generation failed, falling back to text selection")
            await bot_instance.send_selection_message(
                chat_id=user_id,
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
        return await bot_instance.send_poll_message(chat_id=user_id, question=question, options=options)

    ask_poll_func = create_ask_poll(send_poll_func, app.state.pending_human_responses, app.state.poll_id_to_user_id, send_message_func=send_message_func)

    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    transcripts_root = Path(os.getenv("TRANSCRIPTS_PATH", "./transcripts"))

    tavily_api_key = os.getenv("TAVILY_API_KEY")
    tavily_base_url = os.getenv("TAVILY_API_BASE")
    tavily_searcher = create_tavily_searcher(tavily_api_key, tavily_base_url) if tavily_api_key else None

    sensei_agent = create_sensei_agent(
        model=model,
        session_factory=get_session_partial,
        orchestrator_model=orchestrator_model,
        wiki_root=str(wiki_root),
        pending_photos=app.state.pending_photos,
        ask_confirmation=ask_confirmation_func,
        ask_human=ask_human_func,
        ask_selection=ask_selection_func,
        ask_plan_review=ask_plan_review_func,
        ask_poll=ask_poll_func,
        searcher=tavily_searcher,
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

    database_url = os.getenv("DATABASE_URL", "")
    mem0_client = create_mem0_client(database_url) if database_url else None
    memory_service = Mem0MemoryService(mem0_client) if mem0_client else None

    app.state.mem0_client = mem0_client
    app.state.ingest_transcript = create_ingestion_pipeline(model, transcripts_root, wiki_root, orchestrator_model=orchestrator_model)
    app.state.run_wiki_keeper = create_wiki_keeper(orchestrator_model or model, transcripts_root, wiki_root, mem0_client=mem0_client)

    app.state.advisor, app.state.reset_session = create_advisor(
        sensei_agent=sensei_agent,
        get_user_settings_func=services["user_settings"]["get_user_settings"],
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

    handlers = [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
        MessageHandler(filters.PHOTO, photo_handler),
        CallbackQueryHandler(confirmation_handler, pattern=r"^confirm:(accept|cancel):.+$"),
        CallbackQueryHandler(plan_review_handler, pattern=r"^plan_review:.+:(confirm|correct|cancel)$"),
        CallbackQueryHandler(selection_handler, pattern=r"^selection:.+:(\d+|none)$"),
        PollAnswerHandler(poll_answer_handler),
    ]
    if bot_instance.application:
        for handler in handlers:
            bot_instance.application.add_handler(handler)

    app.state.bot = bot_instance
    await bot_instance.initialize()

    weather_scheduler = create_weather_alert_scheduler(
        advisor=app.state.advisor,
        list_all_user_settings_func=services["user_settings"]["list_all_user_settings"],
        send_telegram_message_func=app.state.bot.send_message,
    )
    weekend_scheduler = create_weekend_plan_scheduler(
        advisor=app.state.advisor,
        list_all_user_settings_func=services["user_settings"]["list_all_user_settings"],
        list_planned_works_in_date_range_func=services["cultivation_plan"]["list_planned_works_in_date_range"],
        list_bonsai_func=services["garden"]["list_bonsai"],
        send_telegram_message_func=app.state.bot.send_message,
    )

    yield

    weather_scheduler.shutdown()
    weekend_scheduler.shutdown()
    await bot_instance.shutdown()


configure_logging()

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
app.add_exception_handler(Exception, _generic_exception_handler)
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
app.include_router(weekend_plan_reminder_router, prefix="/api", tags=["weekend_plan_reminder"])
app.include_router(wiki_router, prefix="/api", tags=["wiki"])
app.include_router(transcripts_router, prefix="/api", tags=["transcripts"])
app.include_router(pests_router, prefix="/api", tags=["pests"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
