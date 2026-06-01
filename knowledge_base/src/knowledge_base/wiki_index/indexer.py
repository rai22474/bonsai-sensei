from pathlib import Path
from typing import Callable

from knowledge_base.wiki_index.entry import IndexEntry, extract_abstract, extract_links
from knowledge_base.wiki_index.store import save_entry


async def update_page_index(page_path: str, wiki_root: Path, embed: Callable) -> None:
    """Read page content, build IndexEntry, save to wiki-index/. No-op if page doesn't exist."""
    full_path = wiki_root / page_path
    if not full_path.exists():
        return

    content = full_path.read_text(encoding="utf-8")
    abstract = extract_abstract(content)
    if not abstract.strip():
        return
    links = extract_links(content)
    embedding = await embed(abstract)
    entry = IndexEntry(page_path=page_path, abstract=abstract, links=links, embedding=embedding)
    save_entry(wiki_root, entry)


async def build_full_index(wiki_root: Path, embed: Callable) -> int:
    """Index all .md files in wiki/ (excluding wiki-index/ itself). Returns count of indexed pages."""
    indexed_count = 0
    for md_file in wiki_root.rglob("*.md"):
        relative_path = md_file.relative_to(wiki_root)
        if str(relative_path).startswith("wiki-index/"):
            continue
        await update_page_index(str(relative_path), wiki_root, embed)
        indexed_count += 1
    return indexed_count
