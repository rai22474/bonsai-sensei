import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from functools import partial
from telegram.ext import CommandHandler, MessageHandler, filters

from bonsai_sensei.domain.sensei import create_sensei
from .routes import router
from .telegram_routes import router as telegram_router
from bonsai_sensei.telegram.bot import TelegramBot
from bonsai_sensei.telegram.handlers import start, handle_user_message
from bonsai_sensei.logging_config import configure_logging


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

@asynccontextmanager
async def lifespan(app: FastAPI):  
    message_handler = partial(handle_user_message, message_processor=create_sensei())
    handlers = [
        CommandHandler("start", start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler),
    ]
    bot_instance = TelegramBot(handlers=handlers)

    app.state.bot = bot_instance
    await bot_instance.initialize()
    
    yield
    
    await bot_instance.shutdown()


configure_logging()

app = FastAPI(lifespan=lifespan)
app.add_exception_handler(Exception, _generic_exception_handler)
app.include_router(router)
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
