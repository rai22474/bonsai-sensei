from pathlib import Path
from typing import Callable

from knowledge_base.ingestion.knowledge_card_extractor import create_card_extractor
from knowledge_base.ingestion.transcript_cleaner import create_transcript_cleaner


def create_ingestion_pipeline(
    model: object,
    transcripts_root: Path,
    wiki_root: Path,
    download_transcript: Callable,
    run_wiki_dreamer: Callable,
    orchestrator_model: object = None,
) -> Callable[[str, str], None]:
    """Create an async pipeline that ingests a YouTube video into the wiki.

    Downloads the transcript, cleans it, extracts a knowledge card, then
    triggers the wiki dreamer to integrate the card into the wiki.
    Each step is idempotent: if the output file already exists it is skipped.

    Args:
        model: LLM model used by the cleaner and extractor agents.
        transcripts_root: Root directory for raw, clean and card files.
        wiki_root: Root directory of the wiki.
        download_transcript: Callable that downloads a YouTube transcript to disk.
        run_wiki_dreamer: Dreamer instance shared with the admin bot (includes notify_admin).
        orchestrator_model: Unused, kept for backwards compatibility.

    Returns:
        Async callable: (url, channel, on_step?) -> None
        on_step is an optional async callable(message: str) -> None for progress notifications.
    """
    clean_transcript = create_transcript_cleaner(model)
    extract_card = create_card_extractor(model)

    async def ingest(url: str, channel: str, on_step: Callable | None = None) -> None:
        async def notify(message: str) -> None:
            if on_step:
                await on_step(message)

        await notify("⬇️ Descargando transcript...")
        raw_path = download_transcript(url, channel, transcripts_root)
        await notify("🧹 Limpiando transcript...")
        clean_path = await clean_transcript(raw_path, transcripts_root)
        await notify("🃏 Extrayendo ficha de conocimiento...")
        await extract_card(clean_path, transcripts_root)
        await notify("🌙 Actualizando wiki con el nuevo conocimiento...")
        await run_wiki_dreamer()
        await notify("✅ Ingestión completada.")

    return ingest
