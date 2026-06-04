from pathlib import Path


def write_wiki_page(page_path: str, content: str, wiki_root: Path) -> str:
    """Write or update a wiki page with the given markdown content. Creates the file if it doesn't exist. Returns confirmation."""
    wiki_root_resolved = wiki_root.resolve()
    resolved = (wiki_root_resolved / page_path).resolve()
    if not str(resolved).startswith(str(wiki_root_resolved)):
        return "Error: invalid path"
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")
    return f"Page '{page_path}' written successfully"
