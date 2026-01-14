import logging
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .routes import router

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

app = FastAPI()
app.add_exception_handler(Exception, _generic_exception_handler)
app.include_router(router)
