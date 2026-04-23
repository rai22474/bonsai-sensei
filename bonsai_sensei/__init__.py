import logging
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from functools import partial
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters
from bonsai_sensei.domain.services.advisor import create_advisor
from bonsai_sensei.domain.services.garden.factory import create_gardener_group
from bonsai_sensei.domain.services.human_input import create_ask_confirmation
from bonsai_sensei.domain.services.cultivation.factory import create_cultivation_group
from bonsai_sensei.telegram.messages.gardener_messages import (
    build_create_bonsai_confirmation,
    build_delete_bonsai_confirmation,
    build_update_bonsai_confirmation,
    build_apply_fertilizer_confirmation,
    build_apply_phytosanitary_confirmation,
    build_record_transplant_confirmation,
    build_execute_planned_work_confirmation,
)
from bonsai_sensei.telegram.messages.planning_messages import (
    build_fertilizer_confirmation,
    build_phytosanitary_confirmation,
    build_transplant_confirmation,
    build_delete_confirmation,
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
    build_create_species_confirmation,
    build_delete_species_confirmation,
    build_update_species_confirmation,
)
from bonsai_sensei.domain.services.factory import create_agents, create_sensei_group
from bonsai_sensei.domain.services.storekeeper.factory import create_storekeeper_group
from bonsai_sensei.model_factory import (
    get_cloud_model_factory,
    get_cloud_orchestrator_model_factory,
    get_local_model_factory,
)
from bonsai_sensei.api.species import router as species_router
from bonsai_sensei.api.bonsai import router as bonsai_router
from bonsai_sensei.api.fertilizers import router as fertilizers_router
from bonsai_sensei.api.phytosanitary import router as phytosanitary_router
from bonsai_sensei.api.advice import router as advice_router
from bonsai_sensei.api.weather import router as weather_router
from bonsai_sensei.api.telegram import router as telegram_router
from bonsai_sensei.api.user_settings import router as user_settings_router
from bonsai_sensei.api.planned_works import router as planned_works_router
from bonsai_sensei.api.weekend_plan_reminder import router as weekend_plan_reminder_router
from bonsai_sensei.api.wiki import router as wiki_router
from bonsai_sensei.telegram.error_handler import error_handler
from bonsai_sensei.telegram.handle_confirmation_callback import handle_confirmation_callback
from bonsai_sensei.telegram.handle_user_message import handle_user_message
from bonsai_sensei.telegram.start import start
from bonsai_sensei.telegram.bot import TelegramBot

from bonsai_sensei.domain.services.cultivation.weather.weather_alert_scheduler import create_weather_alert_scheduler
from bonsai_sensei.domain.services.cultivation.plan.weekend_plan_scheduler import create_weekend_plan_scheduler
from bonsai_sensei.domain.user_settings import UserSettings
from bonsai_sensei.logging_config import configure_logging
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.domain import bonsai_history
from bonsai_sensei.domain import user_settings_store
from bonsai_sensei.domain import cultivation_plan
from bonsai_sensei.database.session import get_session, get_engine
from bonsai_sensei.observability import init_telemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


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


def _create_herbarium_service(session_factory):
    return {
        "list_species": partial(
            herbarium.list_species, create_session=session_factory
        ),
        "search_species_by_name": partial(
            herbarium.search_species_by_name, create_session=session_factory
        ),
        "get_species_by_name": partial(
            herbarium.get_species_by_name, create_session=session_factory
        ),
        "create_species": partial(
            herbarium.create_species, create_session=session_factory
        ),
        "update_species": partial(
            herbarium.update_species, create_session=session_factory
        ),
        "delete_species": partial(
            herbarium.delete_species, create_session=session_factory
        ),
    }


def _create_garden_service(session_factory):
    return {
        "list_bonsai": partial(
            garden.list_bonsai, create_session=session_factory
        ),
        "create_bonsai": partial(
            garden.create_bonsai, create_session=session_factory
        ),
        "get_bonsai_by_name": partial(
            garden.get_bonsai_by_name, create_session=session_factory
        ),
        "update_bonsai": partial(
            garden.update_bonsai, create_session=session_factory
        ),
        "delete_bonsai": partial(
            garden.delete_bonsai, create_session=session_factory
        ),
    }


def _create_fertilizer_service(session_factory):
    return {
        "list_fertilizers": partial(
            fertilizer_catalog.list_fertilizers, create_session=session_factory
        ),
        "create_fertilizer": partial(
            fertilizer_catalog.create_fertilizer, create_session=session_factory
        ),
        "get_fertilizer_by_name": partial(
            fertilizer_catalog.get_fertilizer_by_name,
            create_session=session_factory,
        ),
        "delete_fertilizer": partial(
            fertilizer_catalog.delete_fertilizer,
            create_session=session_factory,
        ),
    }


def _create_phytosanitary_service(session_factory):
    return {
        "list_phytosanitary": partial(
            phytosanitary_registry.list_phytosanitary,
            create_session=session_factory,
        ),
        "create_phytosanitary": partial(
            phytosanitary_registry.create_phytosanitary,
            create_session=session_factory,
        ),
        "get_phytosanitary_by_name": partial(
            phytosanitary_registry.get_phytosanitary_by_name,
            create_session=session_factory,
        ),
        "delete_phytosanitary": partial(
            phytosanitary_registry.delete_phytosanitary,
            create_session=session_factory,
        ),
    }


def _create_bonsai_history_service(session_factory):
    return {
        "list_bonsai_events": partial(
            bonsai_history.list_bonsai_events, create_session=session_factory
        ),
        "record_bonsai_event": partial(
            bonsai_history.record_bonsai_event, create_session=session_factory
        ),
    }


def _create_user_settings_service(session_factory):
    return {
        "save_user_settings": partial(
            user_settings_store.save_user_settings, create_session=session_factory
        ),
        "get_user_settings": partial(
            user_settings_store.get_user_settings, create_session=session_factory
        ),
        "list_all_user_settings": partial(
            user_settings_store.list_all_user_settings, create_session=session_factory
        ),
        "delete_user_settings": partial(
            user_settings_store.delete_user_settings, create_session=session_factory
        ),
    }


def _create_cultivation_plan_service(session_factory):
    return {
        "list_planned_works": partial(
            cultivation_plan.list_planned_works, create_session=session_factory
        ),
        "list_planned_works_in_date_range": partial(
            cultivation_plan.list_planned_works_in_date_range, create_session=session_factory
        ),
        "create_planned_work": partial(
            cultivation_plan.create_planned_work, create_session=session_factory
        ),
        "delete_planned_work": partial(
            cultivation_plan.delete_planned_work, create_session=session_factory
        ),
    }


def _save_telegram_chat_id(user_id: str, chat_id: str, save_user_settings):
    save_user_settings(UserSettings(user_id=user_id, telegram_chat_id=chat_id))


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_session_partial = partial(get_session, engine=get_engine())
    init_telemetry()

    app.state.herbarium_service = _create_herbarium_service(get_session_partial)
    app.state.garden_service = _create_garden_service(get_session_partial)
    app.state.fertilizer_service = _create_fertilizer_service(get_session_partial)
    app.state.phytosanitary_service = _create_phytosanitary_service(
        get_session_partial
    )
    app.state.bonsai_history_service = _create_bonsai_history_service(get_session_partial)
    app.state.user_settings_service = _create_user_settings_service(get_session_partial)
    app.state.cultivation_plan_service = _create_cultivation_plan_service(get_session_partial)
    app.state.pending_human_responses = {}
    app.state.active_tasks = {}

    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    model_factory = (
        get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    )
    model = model_factory()
    orchestrator_model = get_cloud_orchestrator_model_factory()() if provider == "cloud" else None

    bot_instance = TelegramBot(error_handler=error_handler)

    async def send_confirmation_func(user_id: str, question: str, confirmation_id: str):
        await bot_instance.send_confirmation_message(chat_id=user_id, text=question, confirmation_id=confirmation_id)

    ask_confirmation_func = create_ask_confirmation(send_confirmation_func, app.state.pending_human_responses)

    cultivation_group_factory = partial(
        create_cultivation_group,
        session_factory=get_session_partial,
        ask_confirmation=ask_confirmation_func,
        build_fertilizer_confirmation=build_fertilizer_confirmation,
        build_phytosanitary_confirmation=build_phytosanitary_confirmation,
        build_transplant_confirmation=build_transplant_confirmation,
        build_delete_confirmation=build_delete_confirmation,
        build_create_species_confirmation=build_create_species_confirmation,
        build_delete_species_confirmation=build_delete_species_confirmation,
        build_update_species_confirmation=build_update_species_confirmation,
        orchestrator_model=orchestrator_model,
    )
    gardener_group_factory = partial(
        create_gardener_group,
        session_factory=get_session_partial,
        ask_confirmation=ask_confirmation_func,
        build_create_bonsai_confirmation=build_create_bonsai_confirmation,
        build_delete_bonsai_confirmation=build_delete_bonsai_confirmation,
        build_update_bonsai_confirmation=build_update_bonsai_confirmation,
        build_apply_fertilizer_confirmation=build_apply_fertilizer_confirmation,
        build_apply_phytosanitary_confirmation=build_apply_phytosanitary_confirmation,
        build_record_transplant_confirmation=build_record_transplant_confirmation,
        build_execute_planned_work_confirmation=build_execute_planned_work_confirmation,
    )
    storekeeper_group_factory = partial(
        create_storekeeper_group,
        session_factory=get_session_partial,
        ask_confirmation=ask_confirmation_func,
        build_create_fertilizer_confirmation=build_create_fertilizer_confirmation,
        build_delete_fertilizer_confirmation=build_delete_fertilizer_confirmation,
        build_update_fertilizer_confirmation=build_update_fertilizer_confirmation,
        build_create_phytosanitary_confirmation=build_create_phytosanitary_confirmation,
        build_delete_phytosanitary_confirmation=build_delete_phytosanitary_confirmation,
        build_update_phytosanitary_confirmation=build_update_phytosanitary_confirmation,
    )
    sensei_group_factory = partial(create_sensei_group, session_factory=get_session_partial, orchestrator_model=orchestrator_model)
    sensei_agent = create_agents(
        model=model,
        create_cultivation_group=cultivation_group_factory,
        create_gardener_group=gardener_group_factory,
        create_storekeeper_group=storekeeper_group_factory,
        create_sensei_group=sensei_group_factory,
    )
    app.state.advisor, app.state.reset_session = create_advisor(
        sensei_agent=sensei_agent,
        get_user_settings_func=app.state.user_settings_service["get_user_settings"],
    )
    save_telegram_chat_id_func = partial(
        _save_telegram_chat_id,
        save_user_settings=app.state.user_settings_service["save_user_settings"],
    )
    users_awaiting_location: set = set()
    message_handler = partial(
        handle_user_message,
        message_processor=app.state.advisor,
        save_telegram_chat_id_func=save_telegram_chat_id_func,
        get_user_settings_func=app.state.user_settings_service["get_user_settings"],
        ask_confirmation=ask_confirmation_func,
        save_user_settings_func=app.state.user_settings_service["save_user_settings"],
        users_awaiting_location=users_awaiting_location,
        pending_human_responses=app.state.pending_human_responses,
    )
    confirmation_handler = partial(
        handle_confirmation_callback,
        pending_human_responses=app.state.pending_human_responses,
        send_cancel_reason_prompt=bot_instance.send_force_reply_message,
    )

    handlers = [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
        CallbackQueryHandler(confirmation_handler, pattern=r"^confirm:(accept|cancel):.+$"),
    ]
    if bot_instance.application:
        for handler in handlers:
            bot_instance.application.add_handler(handler)

    app.state.bot = bot_instance
    await bot_instance.initialize()

    weather_scheduler = create_weather_alert_scheduler(
        advisor=app.state.advisor,
        list_all_user_settings_func=app.state.user_settings_service["list_all_user_settings"],
        send_telegram_message_func=app.state.bot.send_message,
    )
    weekend_scheduler = create_weekend_plan_scheduler(
        advisor=app.state.advisor,
        list_all_user_settings_func=app.state.user_settings_service["list_all_user_settings"],
        list_planned_works_in_date_range_func=app.state.cultivation_plan_service["list_planned_works_in_date_range"],
        list_bonsai_func=app.state.garden_service["list_bonsai"],
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
app.include_router(weekend_plan_reminder_router, prefix="/api", tags=["weekend_plan_reminder"])
app.include_router(wiki_router, prefix="/api", tags=["wiki"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
