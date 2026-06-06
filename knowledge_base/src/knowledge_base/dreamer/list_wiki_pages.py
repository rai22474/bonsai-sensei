from pathlib import Path
from typing import Callable


def create_list_wiki_pages_tool(wiki_root: Path) -> Callable:
    """Create a tool that lists markdown pages within the wiki."""

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
