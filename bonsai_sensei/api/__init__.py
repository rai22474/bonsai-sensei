import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .routes import router
from bonsai_sensei.telegram import bot
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
    await bot.initialize()
    yield
    await bot.shutdown()


configure_logging()

app = FastAPI(lifespan=lifespan)
app.add_exception_handler(Exception, _generic_exception_handler)
app.include_router(router)
