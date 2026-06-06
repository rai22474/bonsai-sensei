import json
import re
import unicodedata
from pathlib import Path
from typing import Callable

from knowledge_base.logging_config import get_logger

logger = get_logger(__name__)

_DEFAULT_LANGUAGES = ["es", "en"]
_OEMBED_URL = "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def create_channel_slug_fetcher(http_client) -> Callable:
    """Create a callable that resolves a YouTube video's channel slug via oEmbed."""

    def fetch_channel_slug(video_id: str) -> str:
        """Fetch the channel slug for a YouTube video using the oEmbed API.

        Extracts the handle from author_url (e.g. @ChannelHandle → channelhandle).
        Falls back to slugified author_name if no handle is present.
        Falls back to 'general' if the oEmbed request fails.
        """
        try:
            response = http_client.get(_OEMBED_URL.format(video_id=video_id))
            response.raise_for_status()
            data = response.json()
            author_url = data.get("author_url", "")
            handle_match = re.search(r"@([^/]+)$", author_url)
            if handle_match:
                return handle_match.group(1).lower()
            author_name = data.get("author_name", "")
            if author_name:
                return _slugify(author_name)
        except Exception:
            logger.warning("oEmbed lookup failed for video_id=%s, using 'general'", video_id)
        return "general"

    return fetch_channel_slug


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


def create_transcript_downloader(transcript_api) -> Callable:
    """Create a transcript downloader bound to a YouTubeTranscriptApi instance."""

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
        fetched = transcript_api.fetch(video_id, languages=resolved_languages)
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

    return download_transcript
