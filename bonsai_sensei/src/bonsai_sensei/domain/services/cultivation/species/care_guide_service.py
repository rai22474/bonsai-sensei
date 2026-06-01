from typing import Callable, Dict, List

SearchResult = Dict[str, object]


def create_care_guide_builder(searcher: Callable[[str], Dict]) -> Callable[[str, str], Dict]:
    """Create a builder that uses the provided searcher to gather care guide info.

    Args:
        searcher: Callable that accepts a search query string and returns a mapping
            with an "answer" and optional "results" list.
    """
    def build(common_name: str, scientific_name: str) -> Dict:
        """Build a care guide payload for a species.

        Args:
            common_name: User-friendly species name to include in the search query.
            scientific_name: Scientific name to disambiguate the search query.
        """
        query = f"{common_name} {scientific_name} bonsai care"
        response = searcher(query)
        answer = str(response.get("answer", "")).strip()
        sources: List[str] = [
            str(item.get("url"))
            for item in response.get("results", [])
            if item.get("url")
        ]
        return {
            "common_name": common_name,
            "scientific_name": scientific_name,
            "summary": answer,
            "watering": None,
            "light": None,
            "soil": None,
            "pruning": None,
            "pests": None,
            "sources": sources,
        }

    return build
