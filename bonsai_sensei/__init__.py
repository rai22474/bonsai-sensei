import logging
import os
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from functools import partial
from telegram.ext import CommandHandler, MessageHandler, filters

from bonsai_sensei.domain.services.advisor import create_advisor
from bonsai_sensei.domain.services.sensei import create_sensei
from google.adk.tools import AgentTool
from bonsai_sensei.domain.services.weather.weather_advisor import create_weather_advisor
from bonsai_sensei.domain.services.species.botanist import create_botanist
from bonsai_sensei.domain.services.species.care_guide_agent import (
    create_care_guide_agent,
)
from bonsai_sensei.domain.services.species.scientific_name_tool import (
    resolve_scientific_name,
    create_scientific_name_resolver,
)
from bonsai_sensei.domain.services.species.scientific_name_translator import (
    translate_to_english,
)
from bonsai_sensei.domain.services.species.scientific_name_searcher import trefle_search
from bonsai_sensei.domain.services.species.tavily_searcher import create_tavily_searcher
from bonsai_sensei.domain.services.species.care_guide_service import (
    create_care_guide_builder,
)
from bonsai_sensei.domain.services.bonsai.gardener import create_gardener
from bonsai_sensei.domain.services.bonsai.bonsai_tools import (
    create_create_bonsai_tool,
    create_delete_bonsai_tool,
    create_get_bonsai_by_name_tool,
    create_list_bonsai_tool,
    create_update_bonsai_tool,
)
from bonsai_sensei.model_factory import (
    get_cloud_model_factory,
    get_local_model_factory,
)
from bonsai_sensei.api.species import router as species_router
from bonsai_sensei.api.telegram import router as telegram_router
from bonsai_sensei.telegram.bot import TelegramBot
from bonsai_sensei.telegram.handlers import start, handle_user_message, error_handler
from bonsai_sensei.logging_config import configure_logging
from bonsai_sensei.domain.services.weather.weather_tool import get_weather
from bonsai_sensei.domain.services.species.herbarium_tools import (
    create_list_species_tool,
)
from bonsai_sensei.domain import garden
from bonsai_sensei.domain import herbarium
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


def _with_tool_metadata(tool, name: str, doc_source):
    tool.__name__ = name
    tool.__doc__ = doc_source.__doc__
    return tool


def _create_list_species_tool(session_factory):
    get_all_species_partial = partial(
        herbarium.get_all_species, create_session=session_factory
    )
    tool = create_list_species_tool(get_all_species_partial)

    tool.__name__ = "list_bonsai_species"

    return tool


def _create_agents(
    model: object,
    list_species_tool,
    create_species_func,
    update_species_func,
    delete_species_func,
    list_bonsai_func,
    create_bonsai_func,
    get_bonsai_by_name_func,
    update_bonsai_func,
    delete_bonsai_func,
    list_species_func,
):
    weather_agent = create_weather_advisor(
        model=model,
        tools=[get_weather, list_species_tool],
    )
    resolve_name_tool = create_scientific_name_resolver(
        translator=translate_to_english,
        searcher=trefle_search,
    )
    resolve_name_tool = _with_tool_metadata(
        resolve_name_tool, "resolve_bonsai_scientific_names", resolve_scientific_name
    )
    tavily_searcher = create_tavily_searcher(os.getenv("TAVILY_API_KEY"))
    care_guide_builder = create_care_guide_builder(tavily_searcher)
    care_guide_builder = _with_tool_metadata(
        care_guide_builder, "build_bonsai_care_guide", care_guide_builder
    )
    care_guide_agent = create_care_guide_agent(
        model=model,
        tools=[care_guide_builder],
    )
    species_agent = create_botanist(
        model=model,
        create_species_func=create_species_func,
        update_species_func=update_species_func,
        delete_species_func=delete_species_func,
        resolve_scientific_name=resolve_name_tool,
        list_species=list_species_tool,
        care_guide_agent=care_guide_agent,
    )
    list_bonsai_tool = create_list_bonsai_tool(
        list_bonsai_func=list_bonsai_func,
        list_species_func=list_species_func,
    )
    list_bonsai_tool.__name__ = "list_bonsai"
    create_bonsai_tool = create_create_bonsai_tool(
        create_bonsai_func=create_bonsai_func,
        list_species_func=list_species_func,
    )
    create_bonsai_tool.__name__ = "create_bonsai"
    get_bonsai_by_name_tool = create_get_bonsai_by_name_tool(
        get_bonsai_by_name_func=get_bonsai_by_name_func,
        list_species_func=list_species_func,
    )
    get_bonsai_by_name_tool.__name__ = "get_bonsai_by_name"
    update_bonsai_tool = create_update_bonsai_tool(
        update_bonsai_func=update_bonsai_func,
        list_species_func=list_species_func,
    )
    update_bonsai_tool.__name__ = "update_bonsai"
    delete_bonsai_tool = create_delete_bonsai_tool(delete_bonsai_func=delete_bonsai_func)
    delete_bonsai_tool.__name__ = "delete_bonsai"
    gardener_agent = create_gardener(
        model=model,
        tools=[
            list_bonsai_tool,
            create_bonsai_tool,
            get_bonsai_by_name_tool,
            update_bonsai_tool,
            delete_bonsai_tool,
        ],
    )
    sensei_tools = [
        AgentTool(weather_agent),
        AgentTool(species_agent),
        AgentTool(gardener_agent),
    ]
    sensei_agent = create_sensei(
        model=model,
        tools=sensei_tools,
    )

    return sensei_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_session_partial = partial(get_session, engine=get_engine())
    setup_monocle_observability()

    app.state.herbarium_service = {
        "list_species": partial(
            herbarium.list_species, create_session=get_session_partial
        ),
        "create_species": partial(
            herbarium.create_species, create_session=get_session_partial
        ),
        "update_species": partial(
            herbarium.update_species, create_session=get_session_partial
        ),
        "delete_species": partial(
            herbarium.delete_species, create_session=get_session_partial
        ),
    }
    app.state.garden_service = {
        "list_bonsai": partial(
            garden.list_bonsai, create_session=get_session_partial
        ),
        "create_bonsai": partial(
            garden.create_bonsai, create_session=get_session_partial
        ),
        "get_bonsai_by_name": partial(
            garden.get_bonsai_by_name, create_session=get_session_partial
        ),
        "update_bonsai": partial(
            garden.update_bonsai, create_session=get_session_partial
        ),
        "delete_bonsai": partial(
            garden.delete_bonsai, create_session=get_session_partial
        ),
    }

    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    model_factory = (
        get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    )
    model = model_factory()
    list_species_tool = _create_list_species_tool(session_factory=get_session_partial)

    sensei_agent = _create_agents(
        model=model,
        list_species_tool=list_species_tool,
        create_species_func=app.state.herbarium_service["create_species"],
        update_species_func=app.state.herbarium_service["update_species"],
        delete_species_func=app.state.herbarium_service["delete_species"],
        list_bonsai_func=app.state.garden_service["list_bonsai"],
        create_bonsai_func=app.state.garden_service["create_bonsai"],
        get_bonsai_by_name_func=app.state.garden_service["get_bonsai_by_name"],
        update_bonsai_func=app.state.garden_service["update_bonsai"],
        delete_bonsai_func=app.state.garden_service["delete_bonsai"],
        list_species_func=app.state.herbarium_service["list_species"],
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
