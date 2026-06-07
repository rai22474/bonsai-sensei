from typing import Callable


def create_search_wiki_knowledge_tool(embed: Callable, search_by_embedding: Callable) -> Callable:
    """Create an async tool that searches wiki pages semantically by topic."""

    async def search_wiki_knowledge(query: str, tool_context=None) -> dict:
        """Search the wiki knowledge base semantically to find existing pages by topic.

        Use this before creating a new page to check if one already exists, and to find
        pages to enrich with new information. Returns top 5 matching pages.
        Includes both global pages and pages belonging to the current user.

        Args:
            query: Natural language query describing the topic and type
                   (e.g. "poda de mantenimiento técnica", "roya enfermedad hongos").

        Returns:
            {"results": [{"page_path": "techniques/poda-de-mantenimiento.md", "abstract": "...", "score": 0.92}, ...]}
        """
        user_id = _resolve_user_id(tool_context)
        query_embedding = await embed(query)
        results = search_by_embedding(query_embedding, top_k=5, user_id=user_id)
        return {
            "results": [
                {"page_path": page_path, "abstract": abstract, "score": round(score, 3)}
                for page_path, abstract, score in results
            ]
        }

    return search_wiki_knowledge


def _resolve_user_id(tool_context) -> str | None:
    if tool_context is None:
        return None
    for context in (tool_context, getattr(tool_context, 'invocation_context', None), getattr(tool_context, 'request_context', None)):
        if context is None:
            continue
        for attr in ('user_id', 'session_id'):
            value = getattr(context, attr, None)
            if value:
                return str(value)
    return None
