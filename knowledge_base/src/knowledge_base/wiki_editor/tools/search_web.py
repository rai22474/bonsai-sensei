from typing import Callable

from tavily import TavilyClient


def create_web_searcher(api_key: str, api_base_url: str | None = None) -> Callable[[str], str]:
    """Create a Tavily web search callable for use as a wiki editor tool."""
    client = TavilyClient(api_key=api_key, api_base_url=api_base_url)

    def search_web(query: str) -> str:
        result = client.search(
            query=query,
            max_results=5,
            include_answer=True,
            include_raw_content=False,
        )
        answer = result.get("answer", "")
        sources = result.get("results", [])
        lines = []
        if answer:
            lines.append(f"Respuesta resumida: {answer}\n")
        for source in sources:
            title = source.get("title", "")
            url = source.get("url", "")
            content = source.get("content", "")
            lines.append(f"## {title}\nURL: {url}\n{content}\n")
        return "\n".join(lines) if lines else "No se encontraron resultados."

    return search_web
