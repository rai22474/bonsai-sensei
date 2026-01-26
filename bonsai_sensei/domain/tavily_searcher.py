from typing import Callable, Dict
from tavily import TavilyClient


def create_tavily_searcher(api_key: str) -> Callable[[str], Dict]:
    if not api_key:
        raise ValueError("TAVILY_API_KEY is required")
    client = TavilyClient(api_key=api_key)

    def search(query: str) -> Dict:
        return client.search(
            query=query,
            max_results=3,
            include_answer=True,
            include_raw_content=False,
        )

    return search
