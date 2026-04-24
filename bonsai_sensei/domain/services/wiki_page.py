from pathlib import Path
from typing import Callable

from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_read_wiki_page_tool(wiki_root: str) -> Callable:
    """Create a tool that reads a wiki page by its relative path.

    Args:
        wiki_root: Absolute path to the root directory of the wiki.
    """
    wiki_root_path = Path(wiki_root).resolve()

    @trace_tool_call
    def read_wiki_page(path: str) -> dict:
        """Read the content of a wiki page by its path relative to the wiki root.

        Use this to read care guides, disease profiles, fertilizer sheets, or any
        other knowledge page. Links in pages use the format [[relative/path.md]]
        and can be followed by calling this tool again with the linked path.

        Args:
            path: Path to the wiki page relative to the wiki root (e.g. 'species/ficus-retusa.md').

        Returns:
            A dict with status 'success' and 'content', or status 'error' and 'message'.
            Output JSON (success): {"status": "success", "content": "<markdown content>"}.
            Output JSON (error): {"status": "error", "message": "page_not_found" | "invalid_path"}.
        """
        resolved = (wiki_root_path / path).resolve()
        if not str(resolved).startswith(str(wiki_root_path)):
            return {"status": "error", "message": "invalid_path"}

        if not resolved.exists():
            return {"status": "error", "message": "page_not_found"}

        return {"status": "success", "content": resolved.read_text(encoding="utf-8")}

    return read_wiki_page
