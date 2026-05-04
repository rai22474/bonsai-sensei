import json
import re
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

from bonsai_sensei.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_LANGUAGES = ["es", "en"]


def extract_video_id(url: str) -> str:
    """Parse a YouTube URL and return the 11-character video ID."""
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",
        r"(?:youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Cannot extract video ID from URL: {url}")


def download_transcript(url: str, channel: str, transcripts_root: Path, languages: list[str] | None = None) -> Path:
    """Download a YouTube transcript and save it as raw JSON.

    Skips download if the raw file already exists.

    Args:
        url: Full YouTube URL.
        channel: Channel slug used as subdirectory name.
        transcripts_root: Root directory for all transcripts.
        languages: Preferred transcript languages in priority order.

    Returns:
        Path to the saved raw JSON file.
    """
    video_id = extract_video_id(url)
    raw_path = transcripts_root / "raw" / channel / f"{video_id}.json"

    if raw_path.exists():
        logger.info("Raw transcript already exists, skipping download: %s", raw_path)
        return raw_path

    resolved_languages = languages or _DEFAULT_LANGUAGES
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=resolved_languages)
    entries = [{"text": snippet.text, "start": snippet.start, "duration": snippet.duration} for snippet in fetched]

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(
            {"video_id": video_id, "url": url, "channel": channel, "entries": entries},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Raw transcript saved: %s (%d entries)", raw_path, len(entries))
    return raw_path
