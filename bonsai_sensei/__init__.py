import logging
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from functools import partial
from telegram.ext import CommandHandler, MessageHandler, filters

from bonsai_sensei.domain.advisor import create_advisor
from bonsai_sensei.domain.sensei_agent import create_sensei_agent
from bonsai_sensei.domain.weather_agent import create_weather_agent
from bonsai_sensei.domain.species_agent import create_species_agent
from bonsai_sensei.model_factory import (
    get_cloud_model_factory,
    get_local_model_factory,
)
from bonsai_sensei.api.species import router as species_router
from bonsai_sensei.api.telegram import router as telegram_router
from bonsai_sensei.telegram.bot import TelegramBot
from bonsai_sensei.telegram.handlers import start, handle_user_message, error_handler
from bonsai_sensei.logging_config import configure_logging
from bonsai_sensei.domain.weather_tool import get_weather
from bonsai_sensei.domain.garden_tool import get_garden_species
from bonsai_sensei.domain import garden
from bonsai_sensei.database.session import get_session, get_engine


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


def _create_garden_tool(session_factory):
    get_all_species_partial = partial(
        garden.get_all_species, create_session=session_factory
    )
    tool = partial(get_garden_species, get_all_species_func=get_all_species_partial)

    tool.__name__ = "get_garden_species"
    tool.__doc__ = get_garden_species.__doc__

    return tool


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_session_partial = partial(get_session, engine=get_engine())
   
    app.state.garden_service = {
        "list_species": partial(garden.list_species, create_session=get_session_partial),
        "create_species": partial(garden.create_species, create_session=get_session_partial),
        "update_species": partial(garden.update_species, create_session=get_session_partial),
        "delete_species": partial(garden.delete_species, create_session=get_session_partial),
    }


    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    model_factory = (
        get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    )
    model = model_factory()
    garden_species_tool = _create_garden_tool(session_factory=get_session_partial)

    weather_agent = create_weather_agent(
        model=model,
        tools=[get_weather, garden_species_tool],
    )
    species_agent = create_species_agent(
        model=model,
        create_species_func=app.state.garden_service["create_species"],
    )
    sensei_agent = create_sensei_agent(
        model=model,
        sub_agents=[weather_agent, species_agent],
    )
    message_handler = partial(
        handle_user_message,
        message_processor=create_advisor(sensei_agent),
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
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
