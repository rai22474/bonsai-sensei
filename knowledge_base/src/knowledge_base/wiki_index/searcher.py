from typing import Callable

import numpy as np

from knowledge_base.wiki_index.entry import IndexEntry


def search_by_embedding(query_embedding: list[float], load_entries: Callable[[], list[IndexEntry]], top_k: int = 5) -> list[tuple[str, str, float]]:
    """Return top_k (page_path, abstract, score) tuples sorted by cosine similarity descending."""
    entries = load_entries()
    if not entries:
        return []

    query_vector = np.array(query_embedding, dtype=np.float32)
    query_norm = np.linalg.norm(query_vector)
    if query_norm == 0:
        return []

    scored = []
    for entry in entries:
        entry_vector = np.array(entry.embedding, dtype=np.float32)
        entry_norm = np.linalg.norm(entry_vector)
        if entry_norm == 0:
            continue
        score = float(np.dot(query_vector, entry_vector) / (query_norm * entry_norm))
        scored.append((entry.page_path, entry.abstract, score))

    scored.sort(key=lambda triple: triple[2], reverse=True)
    return scored[:top_k]
