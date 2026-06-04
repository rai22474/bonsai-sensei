from pathlib import Path


def list_wiki_pages(wiki_root: Path) -> str:
    """List all markdown pages in the wiki. Returns a newline-separated list of page paths."""
    wiki_root_resolved = wiki_root.resolve()
    if not wiki_root_resolved.exists():
        return ""
    pages = sorted(str(page.relative_to(wiki_root_resolved)) for page in wiki_root_resolved.rglob("*.md"))
    return "\n".join(pages)
