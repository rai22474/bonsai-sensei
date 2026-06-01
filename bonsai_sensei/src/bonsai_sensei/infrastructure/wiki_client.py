import httpx
from typing import Callable



def create_http_search_wiki_knowledge_tool(kb_base_url: str) -> Callable:
    """Create an async tool that searches the wiki via HTTP call to knowledge_base service."""

    async def search_wiki_knowledge(query: str) -> dict:
        """Search the wiki knowledge base semantically. Use this to find relevant pages about species, fertilizers, techniques, pests, or any bonsai topic before answering questions. Returns top 5 matching pages with their paths and abstracts."""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{kb_base_url}/api/wiki/index/search", json={"query": query})
            response.raise_for_status()
            return response.json()

    return search_wiki_knowledge


def create_http_read_wiki_page_tool(kb_base_url: str) -> Callable:
    """Create a tool that reads a wiki page via HTTP call to knowledge_base service."""

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
        try:
            with httpx.Client() as client:
                response = client.get(f"{kb_base_url}/api/wiki", params={"path": path})
                if response.status_code == 404:
                    return {"status": "error", "message": "page_not_found"}
                if response.status_code == 400:
                    return {"status": "error", "message": "invalid_path"}
                response.raise_for_status()
                return {"status": "success", "content": response.json()["content"]}
        except httpx.UnsupportedProtocol:
            return {"status": "error", "message": "page_not_found"}

    return read_wiki_page


def create_http_write_wiki_page_tool(kb_base_url: str) -> Callable:
    """Create a tool that writes a wiki page via HTTP call to knowledge_base service."""

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
        with httpx.Client() as client:
            response = client.put(f"{kb_base_url}/api/wiki", json={"path": path, "content": content})
            if response.status_code == 400:
                return {"status": "error", "message": "invalid_path"}
            response.raise_for_status()
            return {"status": "success", "path": path}

    return write_wiki_page


def create_http_list_wiki_files_tool(kb_base_url: str) -> Callable:
    """Create a function that lists wiki files via HTTP call to knowledge_base service."""

    def list_wiki_files(directory: str, pattern: str = "*.md") -> list[str]:
        """List wiki files in a directory matching a glob pattern.

        Args:
            directory: Directory path relative to wiki root.
            pattern: Glob pattern to match files (default: '*.md').

        Returns:
            A sorted list of file paths relative to the wiki root.
        """
        with httpx.Client() as client:
            response = client.get(f"{kb_base_url}/api/wiki/files", params={"directory": directory, "pattern": pattern})
            if response.status_code != 200:
                return []
            return response.json()

    return list_wiki_files
