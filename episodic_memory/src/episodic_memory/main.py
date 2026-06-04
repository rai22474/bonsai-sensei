import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from episodic_memory.api.episodes import router
from episodic_memory.graphiti_store import create_graphiti_store
from episodic_memory.logging_config import configure_logging, get_logger

load_dotenv()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    falkordb_host = os.getenv("FALKORDB_HOST", "localhost")
    falkordb_port = int(os.getenv("FALKORDB_PORT", "6379"))
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    store = create_graphiti_store(
        host=falkordb_host,
        port=falkordb_port,
        gemini_api_key=gemini_api_key,
        model=gemini_model,
    )
    await store.initialize()
    application.state.store = store
    logger.info("Episodic memory service started (FalkorDB at %s:%d)", falkordb_host, falkordb_port)

    yield

    await store.close()
    logger.info("Episodic memory service stopped")


app = FastAPI(title="Episodic Memory", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
