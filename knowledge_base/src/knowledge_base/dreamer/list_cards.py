from pathlib import Path
from typing import Callable


def create_list_cards_tool(transcripts_root: Path) -> Callable:
    """Create a tool that lists knowledge cards extracted from YouTube videos."""

    cards_root = (transcripts_root / "cards").resolve()

    def list_cards(channel: str = "") -> dict:
        """List all knowledge cards extracted from YouTube videos.

        Args:
            channel: Channel slug to filter by (e.g. "kingii", "mini-bonsai").
                     Use "" to list cards from all channels.

        Returns:
            {"status": "success", "cards": ["channel/video_id.md", ...]} or
            {"status": "error", "message": "invalid_path"}.
        """
        target = (cards_root / channel).resolve() if channel else cards_root
        if not str(target).startswith(str(cards_root)):
            return {"status": "error", "message": "invalid_path"}
        if not target.exists():
            return {"status": "success", "cards": []}
        cards = sorted(str(card.relative_to(cards_root)) for card in target.rglob("*.md"))
        return {"status": "success", "cards": cards}

    return list_cards
