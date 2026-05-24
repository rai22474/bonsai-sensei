from pathlib import Path
from typing import Callable

from bonsai_sensei.domain.services.tool_tracer import trace_tool_call
from bonsai_sensei.knowledge_base import wiki_git


def create_write_wiki_page_tool(wiki_root: str | Path) -> Callable:
    """Create a tool that writes content to a wiki page at the given relative path.

    Args:
        wiki_root: Absolute path to the root directory of the wiki.
    """
    wiki_root_path = Path(wiki_root).resolve()

    def write_wiki_page(path: str, content: str) -> dict:
        """Write content to a wiki page at the given path relative to the wiki root.

        Creates parent directories if they do not exist.

        Args:
            path: Path relative to wiki root (e.g. 'species/ficus-retusa.md').
            content: Full markdown content to write to the page.

        Returns:
            A dict with status 'success' and 'path', or status 'error' and 'message'.
            Output JSON (success): {"status": "success", "path": "<relative_path>"}.
            Output JSON (error): {"status": "error", "message": "invalid_path"}.
        """
        resolved = (wiki_root_path / path).resolve()
        if not str(resolved).startswith(str(wiki_root_path)):
            return {"status": "error", "message": "invalid_path"}
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return {"status": "success", "path": path}

    return write_wiki_page


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


def create_list_wiki_files_tool(wiki_root: str | Path) -> Callable:
    """Create a function that lists wiki files in a directory matching a glob pattern."""
    wiki_root_path = Path(wiki_root).resolve()

    def list_wiki_files(directory: str, pattern: str = "*.md") -> list[str]:
        """List wiki files in a directory matching a glob pattern.

        Args:
            directory: Directory path relative to wiki root.
            pattern: Glob pattern to match files (default: '*.md').

        Returns:
            A sorted list of file paths relative to the wiki root.
        """
        target = (wiki_root_path / directory).resolve()
        if not str(target).startswith(str(wiki_root_path)):
            return []
        if not target.is_dir():
            return []
        return [
            str(path.relative_to(wiki_root_path))
            for path in sorted(target.glob(pattern))
        ]

    return list_wiki_files


def create_get_wiki_page_diff_tool(wiki_root: str | Path) -> Callable:
    """Create a tool that returns the diff introduced by the last keeper commit for a wiki page."""
    wiki_root_path = Path(wiki_root).resolve()

    def get_wiki_page_diff(page_path: str) -> dict:
        """Return the changes introduced by the last keeper run for a specific wiki page.

        Use this after the keeper has run to review what changed in a given page.
        The diff is in unified format (lines starting with '+' were added, '-' removed).

        Args:
            page_path: Path to the wiki page relative to the wiki root (e.g. 'bonsai/goku/index.md').

        Returns:
            Output JSON (success): {"status": "success", "diff": "<unified diff text>"}.
            Output JSON (no_changes): {"status": "no_changes"}.
            Output JSON (error): {"status": "error", "message": "no_git_history" | "invalid_path"}.
        """
        resolved = (wiki_root_path / page_path).resolve()
        if not str(resolved).startswith(str(wiki_root_path)):
            return {"status": "error", "message": "invalid_path"}
        if not (wiki_root_path / ".git").exists():
            return {"status": "error", "message": "no_git_history"}
        diff = wiki_git.get_page_diff(wiki_root_path, page_path, "HEAD")
        if not diff.strip():
            return {"status": "no_changes"}
        return {"status": "success", "diff": diff}

    return get_wiki_page_diff
