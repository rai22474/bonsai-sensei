import logging
import os
import traceback
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from telegram.ext import CallbackQueryHandler

from knowledge_base.admin_config import load_admin_chat_id, load_review_sessions
from knowledge_base.api.transcripts import router as transcripts_router
from knowledge_base.api.wiki import router as wiki_router
from knowledge_base.api.wiki_index import router as wiki_index_router
from knowledge_base.api.wiki_review import router as wiki_review_router
from knowledge_base.dreamer.runner import create_wiki_dreamer
from knowledge_base.dreamer.scheduler import create_wiki_dreamer_scheduler
from knowledge_base.ingestion.factory import create_ingestion_pipeline
from knowledge_base.ingestion.transcript_loader import create_transcript_downloader
from knowledge_base.logging_config import configure_logging
from knowledge_base.telegram.admin_bot import AdminBotManager
from knowledge_base.telegram.bot import TelegramBot
from knowledge_base.telegram.handle_wiki_review_callback import handle_wiki_review_callback
from knowledge_base.wiki_editor.runner import create_wiki_editor
from knowledge_base.wiki_index.embedder import create_embed_text
from knowledge_base.mcp.wiki_server import create_wiki_mcp_server, build_mcp_starlette_app

from youtube_transcript_api import YouTubeTranscriptApi


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
    wiki_root = Path(os.getenv("WIKI_PATH", "./wiki"))
    transcripts_root = Path(os.getenv("TRANSCRIPTS_PATH", "./transcripts"))

    embed_text = create_embed_text(os.getenv("GEMINI_API_KEY", ""))
    app.state.embed_text = embed_text

    from honcho import Honcho
    honcho_api_key = os.getenv("HONCHO_API_KEY", "")
    honcho_workspace_id = os.getenv("HONCHO_WORKSPACE_ID", "bonsai-sensei")
    honcho_base_url = os.getenv("HONCHO_BASE_URL")
    honcho_client = Honcho(api_key=honcho_api_key, workspace_id=honcho_workspace_id, base_url=honcho_base_url).aio if honcho_api_key else None

    admin_bot_instance = TelegramBot(token=os.getenv("ADMIN_TELEGRAM_BOT_TOKEN"))
    admin_chat_id = load_admin_chat_id(wiki_root) or os.getenv("ADMIN_TELEGRAM_CHAT_ID")

    app.state.wiki_review_sessions = load_review_sessions(wiki_root)

    provider = os.getenv("MODEL_PROVIDER", "cloud").lower()
    from knowledge_base.model_factory import get_cloud_model_factory, get_local_model_factory, get_cloud_orchestrator_model_factory
    model_factory = get_local_model_factory() if provider == "local" else get_cloud_model_factory()
    model = model_factory()
    orchestrator_model = get_cloud_orchestrator_model_factory()() if provider == "cloud" else None
    effective_model = orchestrator_model or model


    download_transcript = create_transcript_downloader(YouTubeTranscriptApi())
    app.state.ingest_transcript = create_ingestion_pipeline(
        effective_model, transcripts_root, wiki_root,
        download_transcript=download_transcript,
        orchestrator_model=orchestrator_model,
    )

    wiki_review_handler = partial(
        handle_wiki_review_callback,
        wiki_review_sessions=app.state.wiki_review_sessions,
        send_page_diff_message=admin_bot_instance.send_wiki_page_diff_message,
        send_review_status=admin_bot_instance.send_wiki_review_status,
        wiki_root=wiki_root,
        admin_chat_id=admin_chat_id,
    )

    admin_bot_manager = AdminBotManager(
        bot=admin_bot_instance,
        wiki_root=wiki_root,
        wiki_review_sessions=app.state.wiki_review_sessions,
        run_wiki_dreamer=None,
        ingest_transcript=app.state.ingest_transcript,
        wiki_review_handler=wiki_review_handler,
        honcho_client=honcho_client,
        honcho_workspace_id=honcho_workspace_id,
        embed=embed_text,
    )
    admin_bot_manager.set_chat_id(admin_chat_id)
    app.state.admin_bot_manager = admin_bot_manager

    app.state.run_wiki_dreamer = create_wiki_dreamer(
        effective_model,
        transcripts_root,
        wiki_root,
        notify_admin=admin_bot_manager.notify_wiki_changes,
        embed=embed_text,
        honcho_client=honcho_client,
        honcho_workspace_id=honcho_workspace_id,
    )
    admin_bot_manager.set_run_wiki_dreamer(app.state.run_wiki_dreamer)

    app.state.wiki_editor = create_wiki_editor(
        effective_model,
        wiki_root,
        notify_admin=admin_bot_manager.notify_wiki_changes,
        embed=embed_text,
    )
    admin_bot_manager._wiki_editor = app.state.wiki_editor

    if admin_bot_instance.application:
        for handler in admin_bot_manager.build_handlers():
            admin_bot_instance.application.add_handler(handler)

    app.state.admin_bot = admin_bot_instance
    await admin_bot_instance.initialize()
    await admin_bot_instance.register_commands([
        ("start", "Registrar este chat como canal admin"),
        ("dreamer", "Lanzar el wiki dreamer manualmente"),
        ("index", "Reconstruir el índice de búsqueda de la wiki"),
        ("feedback", "Incorporar una corrección en la wiki"),
    ])

    wiki_dreamer_interval = int(os.getenv("WIKI_DREAMER_INTERVAL_SECONDS", str(30 * 60)))
    wiki_dreamer_scheduler = create_wiki_dreamer_scheduler(
        run_wiki_dreamer=app.state.run_wiki_dreamer,
        interval_seconds=wiki_dreamer_interval,
    )

    yield

    wiki_dreamer_scheduler.shutdown()
    await admin_bot_instance.shutdown()


configure_logging()

app = FastAPI(lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
app.add_exception_handler(Exception, _generic_exception_handler)
app.include_router(wiki_router, prefix="/api", tags=["wiki"])
app.include_router(wiki_review_router, prefix="/api", tags=["wiki-review"])
app.include_router(wiki_index_router, prefix="/api", tags=["wiki-index"])
app.include_router(transcripts_router, prefix="/api", tags=["transcripts"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics_endpoint():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


_wiki_mcp_server, _wiki_sse_transport = create_wiki_mcp_server(
    Path(os.getenv("WIKI_PATH", "./wiki"))
)
app.mount("/mcp", build_mcp_starlette_app(_wiki_mcp_server, _wiki_sse_transport))
