from pathlib import Path
from typing import Callable

from bonsai_sensei.knowledge_base.ingestion.channel_page_writer import create_channel_page_writer
from bonsai_sensei.knowledge_base.ingestion.knowledge_card_extractor import create_card_extractor
from bonsai_sensei.knowledge_base.ingestion.transcript_cleaner import create_transcript_cleaner
from bonsai_sensei.knowledge_base.ingestion.transcript_loader import download_transcript
from bonsai_sensei.knowledge_base.keeper.runner import create_wiki_keeper


def create_ingestion_pipeline(
    model: object,
    transcripts_root: Path,
    wiki_root: Path,
) -> Callable[[str, str], None]:
    """Create an async pipeline that ingests a YouTube video into the wiki.

    Downloads the transcript, cleans it, extracts a knowledge card, writes
    an official wiki page under wiki/channels/{channel}/{video_id}.md, then
    triggers the wiki keeper to maintain coherence across all wiki pages.
    Each step is idempotent: if the output file already exists it is skipped.

    Args:
        model: LLM model used by the cleaner, extractor, page writer and keeper agents.
        transcripts_root: Root directory for raw, clean and card files.
        wiki_root: Root directory of the wiki where channel pages are written.

    Returns:
        Async callable: (url, channel) -> None
    """
    clean_transcript = create_transcript_cleaner(model)
    extract_card = create_card_extractor(model)
    write_channel_page = create_channel_page_writer(model)
    run_wiki_keeper = create_wiki_keeper(model, transcripts_root, wiki_root)

    async def ingest(url: str, channel: str) -> None:
        raw_path = download_transcript(url, channel, transcripts_root)
        clean_path = await clean_transcript(raw_path, transcripts_root)
        card_path = await extract_card(clean_path, transcripts_root)
        await write_channel_page(card_path, wiki_root)
        await run_wiki_keeper()

    return ingest
