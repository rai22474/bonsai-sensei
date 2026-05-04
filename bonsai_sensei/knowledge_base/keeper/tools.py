from pathlib import Path
from typing import Callable


def create_list_wiki_pages_tool(wiki_root: Path) -> Callable:
    wiki_root_resolved = wiki_root.resolve()

    def list_wiki_pages(directory: str = "") -> dict:
        """List all markdown pages within a wiki directory.

        Args:
            directory: Path relative to wiki root (e.g. "species", "fertilizers").
                       Use "" to list all pages in the entire wiki.

        Returns:
            {"status": "success", "pages": ["relative/path.md", ...]} or
            {"status": "error", "message": "invalid_path"}.
        """
        target = (wiki_root / directory).resolve() if directory else wiki_root_resolved
        if not str(target).startswith(str(wiki_root_resolved)):
            return {"status": "error", "message": "invalid_path"}
        if not target.exists():
            return {"status": "success", "pages": []}
        pages = sorted(str(page.relative_to(wiki_root)) for page in target.rglob("*.md"))
        return {"status": "success", "pages": pages}

    return list_wiki_pages


def create_list_cards_tool(transcripts_root: Path) -> Callable:
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


def create_read_card_tool(transcripts_root: Path) -> Callable:
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
