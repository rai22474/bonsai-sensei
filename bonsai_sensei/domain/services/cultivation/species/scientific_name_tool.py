from typing import Callable, List, Dict

from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


Translator = Callable[[str], str]
Searcher = Callable[[str], List[Dict[str, str]]]


@limit_tool_calls(agent_name="botanist")
def resolve_scientific_name(
    common_name: str,
    translator: Translator,
    searcher: Searcher,
) -> Dict:
    """Resolve scientific names for a common name via translation and lookup.

    Args:
        common_name: Common name to resolve.
        translator: Translator used to normalize the query.
        searcher: Searcher used to fetch candidates.

    Returns:
        A JSON-ready dictionary with the resolution results.
    """
    return _resolve_scientific_name(
        common_name=common_name,
        translator=translator,
        searcher=searcher,
    )


def create_scientific_name_resolver(
    translator: Translator,
    searcher: Searcher,
) -> Callable[[str], Dict]:
    @limit_tool_calls(agent_name="botanist")
    def resolve(common_name: str) -> Dict:
        """Resolve scientific names for a common name using configured services.

        Args:
            common_name: Common name to resolve.

        Returns:
            A JSON-ready dictionary with the resolution results.
        """
        return _resolve_scientific_name(
            common_name=common_name,
            translator=translator,
            searcher=searcher,
        )

    return resolve


def _resolve_scientific_name(
    common_name: str,
    translator: Translator,
    searcher: Searcher,
) -> Dict:
    if not common_name:
        return _empty_result(common_name)

    translated_name = translator(common_name)

    search_term = translated_name or common_name
    scientific_names = _extract_scientific_names(searcher(search_term))

    if not scientific_names:
        return _empty_result(common_name)

    return {
        "common_name": common_name,
        "scientific_names": scientific_names,
    }


def _empty_result(common_name: str) -> Dict:
    return {
        "common_name": common_name,
        "scientific_names": [],
    }


def _extract_scientific_names(results: List[Dict[str, str]]) -> List[str]:
    names: List[str] = []
    for entry in results:
        scientific_name = entry.get("scientific_name")
        if scientific_name and scientific_name not in names:
            names.append(scientific_name)

    return names
