from typing import Callable


def create_search_wiki_knowledge_tool(embed: Callable, search_index: Callable) -> Callable:
    """Create an async tool that semantically searches the wiki knowledge base.

    Returns a callable that the sensei agent can call to find relevant wiki pages
    by semantic similarity. Results include page path and abstract for each match.
    embed: async callable (text -> embedding vector)
    search_index: sync callable (embedding -> list of (page_path, abstract, score))
    """

    async def search_wiki_knowledge(query: str) -> dict:
        """Search the wiki knowledge base semantically. Use this to find relevant pages about species, fertilizers, techniques, pests, or any bonsai topic before answering questions. Returns top 5 matching pages with their paths and abstracts."""
        query_embedding = await embed(query)
        results = search_index(query_embedding)
        return {
            "results": [
                {"page_path": page_path, "abstract": abstract, "score": round(score, 3)}
                for page_path, abstract, score in results
            ]
        }

    return search_wiki_knowledge
