import unicodedata
from pathlib import Path
from typing import Callable


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def create_find_existing_wiki_page_tool(
    embed: Callable,
    search_by_embedding: Callable,
    wiki_root: Path,
) -> Callable:
    """Create an async tool that resolves an entity name to an existing wiki page."""

    wiki_root_resolved = wiki_root.resolve()

    async def find_existing_wiki_page(entity_name: str, directory: str) -> dict:
        """Find an existing wiki page for a named entity before creating a new one.

        Searches semantically and confirms the match by checking that the entity name
        appears in the page content. Handles aliases (scientific vs. common names) because
        it reads the actual file rather than trusting the slug alone.

        Args:
            entity_name: Name of the entity to look for (e.g. "Acer buergerianum",
                         "poda de mantenimiento", "roya").
            directory: Wiki subdirectory to restrict the search (e.g. "species",
                       "techniques", "diseases").

        Returns:
            {"found": True, "page_path": "species/arce-tridente-japon-s.md"} if a
            matching page exists, or {"found": False} if none found.
        """
        query_embedding = await embed(entity_name)
        results = search_by_embedding(query_embedding, top_k=10)

        normalized_name = _normalize(entity_name)
        expected_prefix = directory.strip("/") + "/"

        for page_path, _abstract, score in results:
            if score < 0.5:
                break
            if not page_path.startswith(expected_prefix):
                continue
            full_path = (wiki_root_resolved / page_path).resolve()
            if not str(full_path).startswith(str(wiki_root_resolved)):
                continue
            if not full_path.exists():
                continue
            content = full_path.read_text(encoding="utf-8")
            if normalized_name in _normalize(content):
                return {"found": True, "page_path": page_path}

        return {"found": False}

    return find_existing_wiki_page
