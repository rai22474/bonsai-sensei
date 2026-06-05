from pathlib import Path
from typing import Callable, Optional

from knowledge_base.wiki_index.entry import IndexEntry, extract_abstract, extract_links


async def update_page_index(
    page_path: str,
    wiki_root: Path,
    embed: Callable,
    save_entry: Optional[Callable[[IndexEntry], None]] = None,
) -> None:
    """Read page content, build IndexEntry, persist via save_entry. No-op if page missing or save_entry is None."""
    if save_entry is None:
        return
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
    save_entry(entry)


async def build_full_index(
    wiki_root: Path,
    embed: Callable,
    save_entry: Optional[Callable[[IndexEntry], None]] = None,
) -> int:
    """Index all .md files under wiki_root. Returns count of indexed pages."""
    if save_entry is None:
        return 0
    indexed_count = 0
    for md_file in wiki_root.rglob("*.md"):
        relative_path = md_file.relative_to(wiki_root)
        await update_page_index(str(relative_path), wiki_root, embed, save_entry)
        indexed_count += 1
    return indexed_count
