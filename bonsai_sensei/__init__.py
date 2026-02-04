import logging
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from functools import partial
from telegram.ext import CommandHandler, MessageHandler, filters

from bonsai_sensei.domain.services.advisor import create_advisor
from bonsai_sensei.domain.services.bonsai.factory import create_gardener_group
from bonsai_sensei.domain.services.cultivation.factory import create_cultivation_group
from bonsai_sensei.domain.services.factory import create_agents, create_sensei_group
from bonsai_sensei.domain.services.storekeeper.factory import create_storekeeper_group
from bonsai_sensei.model_factory import (
    get_cloud_model_factory,
    get_local_model_factory,
)
from bonsai_sensei.api.species import router as species_router
from bonsai_sensei.api.bonsai import router as bonsai_router
from bonsai_sensei.api.fertilizers import router as fertilizers_router
from bonsai_sensei.api.phytosanitary import router as phytosanitary_router
from bonsai_sensei.api.advice import router as advice_router
from bonsai_sensei.api.weather import router as weather_router
from bonsai_sensei.api.telegram import router as telegram_router
from bonsai_sensei.telegram.bot import TelegramBot
from bonsai_sensei.telegram.handlers import start, handle_user_message, error_handler
from bonsai_sensei.logging_config import configure_logging
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
from bonsai_sensei.domain import fertilizer_catalog
from bonsai_sensei.domain import phytosanitary_registry
from bonsai_sensei.database.session import get_session, get_engine
from bonsai_sensei.observability import setup_monocle_observability


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
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_session_partial = partial(get_session, engine=get_engine())
    setup_monocle_observability()

    app.state.herbarium_service = _create_herbarium_service(get_session_partial)
    app.state.garden_service = _create_garden_service(get_session_partial)
    app.state.fertilizer_service = _create_fertilizer_service(get_session_partial)
    app.state.phytosanitary_service = _create_phytosanitary_service(
        get_session_partial
    )

    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    model_factory = (
        get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    )
    model = model_factory()
    cultivation_group_factory = partial(
        create_cultivation_group,
        session_factory=get_session_partial,
    )
    gardener_group_factory = partial(
        create_gardener_group,
        session_factory=get_session_partial,
    )
    storekeeper_group_factory = partial(
        create_storekeeper_group,
        session_factory=get_session_partial,
    )
    sensei_group_factory = partial(create_sensei_group)
    sensei_agent = create_agents(
        model=model,
        create_cultivation_group=cultivation_group_factory,
        create_gardener_group=gardener_group_factory,
        create_storekeeper_group=storekeeper_group_factory,
        create_sensei_group=sensei_group_factory,
    )
    app.state.advisor = create_advisor(sensei_agent)
    message_handler = partial(
        handle_user_message,
        message_processor=app.state.advisor,
    )
    handlers = [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
    ]
    bot_instance = TelegramBot(handlers=handlers, error_handler=error_handler)

    app.state.bot = bot_instance
    await bot_instance.initialize()

    yield

    await bot_instance.shutdown()


configure_logging()

app = FastAPI(lifespan=lifespan)
app.add_exception_handler(Exception, _generic_exception_handler)
app.include_router(species_router, prefix="/api", tags=["species"])
app.include_router(bonsai_router, prefix="/api", tags=["bonsai"])
app.include_router(fertilizers_router, prefix="/api", tags=["fertilizers"])
app.include_router(phytosanitary_router, prefix="/api", tags=["phytosanitary"])
app.include_router(advice_router, prefix="/api", tags=["advice"])
app.include_router(weather_router, prefix="/api", tags=["weather"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
