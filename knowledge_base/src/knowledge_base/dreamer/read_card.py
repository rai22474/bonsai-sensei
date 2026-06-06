from pathlib import Path
from typing import Callable


def create_read_card_tool(transcripts_root: Path) -> Callable:
    """Create a tool that reads a knowledge card by its path."""

    cards_root = (transcripts_root / "cards").resolve()

    def read_card(path: str) -> dict:
        """Read the content of a knowledge card by its path.

        Args:
            path: Path relative to the cards root (e.g. "kingii/pjpReIDRWvo.md").

        Returns:
            {"status": "success", "content": "<markdown>"} or
            {"status": "error", "message": "card_not_found" | "invalid_path"}.
        """
        resolved = (cards_root / path).resolve()
        if not str(resolved).startswith(str(cards_root)):
            return {"status": "error", "message": "invalid_path"}
        if not resolved.exists():
            return {"status": "error", "message": "card_not_found"}
        return {"status": "success", "content": resolved.read_text(encoding="utf-8")}

    return read_card
