from http_client import delete, get, post, put


def write_wiki_page(path: str, content: str) -> dict:
    """Write a wiki page via REST API."""
    return put("/api/wiki", {"path": path, "content": content})


def read_wiki_page(path: str) -> dict | None:
    """Read a wiki page via REST API. Returns None if not found."""
    try:
        return get(f"/api/wiki?path={path}")
    except Exception:
        return None


def list_wiki_files(directory: str = "", pattern: str = "*.md") -> list[str]:
    """List wiki files via REST API."""
    result = get(f"/api/wiki/files?directory={directory}&pattern={pattern}")
    if isinstance(result, list):
        return result
    return []


def delete_wiki_page(path: str) -> dict:
    """Delete a wiki page via REST API."""
    return delete(f"/api/wiki?path={path}")


def search_wiki(query: str, top_k: int = 5) -> list[dict]:
    """Search wiki via REST semantic search."""
    result = post("/api/wiki/index/search", {"query": query, "top_k": top_k})
    return (result or {}).get("results", [])
