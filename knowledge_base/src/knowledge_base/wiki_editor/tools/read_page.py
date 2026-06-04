from pathlib import Path


def read_wiki_page(page_path: str, wiki_root: Path) -> str:
    """Read the content of a wiki page. Returns the markdown content or an error message if not found."""
    wiki_root_resolved = wiki_root.resolve()
    resolved = (wiki_root_resolved / page_path).resolve()
    if not str(resolved).startswith(str(wiki_root_resolved)):
        return "Error: invalid path"
    if not resolved.exists():
        return f"Error: page '{page_path}' not found"
    return resolved.read_text(encoding="utf-8")
