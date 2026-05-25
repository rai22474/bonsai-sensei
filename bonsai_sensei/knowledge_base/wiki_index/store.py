import json
from pathlib import Path

from bonsai_sensei.knowledge_base.wiki_index.entry import IndexEntry

_INDEX_DIR = "wiki-index"


def save_entry(wiki_root: Path, entry: IndexEntry) -> None:
    """Save an index entry to wiki-index/<page_path>.json (creates dirs as needed)."""
    index_file = _entry_path(wiki_root, entry.page_path)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(
        json.dumps({
            "page_path": entry.page_path,
            "abstract": entry.abstract,
            "links": entry.links,
            "embedding": entry.embedding,
        }),
        encoding="utf-8",
    )


def load_entry(wiki_root: Path, page_path: str) -> IndexEntry | None:
    """Load a single index entry. Returns None if not found."""
    index_file = _entry_path(wiki_root, page_path)
    if not index_file.exists():
        return None
    data = json.loads(index_file.read_text(encoding="utf-8"))
    return IndexEntry(
        page_path=data["page_path"],
        abstract=data["abstract"],
        links=data["links"],
        embedding=data["embedding"],
    )


def load_all_entries(wiki_root: Path) -> list[IndexEntry]:
    """Load all index entries from wiki-index/. Returns empty list if dir doesn't exist."""
    index_dir = wiki_root / _INDEX_DIR
    if not index_dir.exists():
        return []
    return [
        IndexEntry(
            page_path=data["page_path"],
            abstract=data["abstract"],
            links=data["links"],
            embedding=data["embedding"],
        )
        for json_file in index_dir.rglob("*.json")
        for data in [json.loads(json_file.read_text(encoding="utf-8"))]
    ]


def _entry_path(wiki_root: Path, page_path: str) -> Path:
    return wiki_root / _INDEX_DIR / (page_path + ".json")
