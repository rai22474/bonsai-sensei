from typing import Callable
import re

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_fetch_fertilizer_info_tool(searcher: Callable[[str], dict]):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def fetch_fertilizer_info(name: str) -> dict:
        """Fetch fertilizer info and return JSON with usage sheet and recommended amount.

        Args:
            name: Fertilizer name to look up.

        Returns:
            A JSON-ready dictionary with the fetched fertilizer info.

        Output JSON: {"status":"success","fertilizer":{"name","usage_sheet","recommended_amount","sources"}}.
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        query = f"{name} bonsai dosis de uso ficha tecnica fertilizante"
        response = searcher(query)
        answer = str(response.get("answer", "")).strip()
        sources = [
            str(item.get("url"))
            for item in response.get("results", [])
            if item.get("url")
        ]
        recommended_amount = _extract_recommended_amount(answer)
        usage_sheet = answer or "No data available."
        return {
            "status": "success",
            "fertilizer": {
                "name": name,
                "usage_sheet": usage_sheet,
                "recommended_amount": recommended_amount,
                "sources": sources,
            },
        }

    return fetch_fertilizer_info


def create_list_fertilizers_tool(list_fertilizers_func: Callable[[], list[Fertilizer]]):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def list_fertilizers() -> dict:
        """Return JSON with all registered fertilizers.

        Returns:
            A JSON-ready dictionary with the fertilizer list.

        Output JSON: {"status":"success","fertilizers":[{"id","name","usage_sheet","recommended_amount"}]}.
        """
        fertilizers = list_fertilizers_func()
        items = [
            {
                "id": fertilizer.id,
                "name": fertilizer.name,
                "usage_sheet": fertilizer.usage_sheet,
                "recommended_amount": fertilizer.recommended_amount,
                "sources": fertilizer.sources,
            }
            for fertilizer in fertilizers
        ]
        return {"status": "success", "fertilizers": items}

    return list_fertilizers


def create_get_fertilizer_by_name_tool(
    get_fertilizer_by_name_func: Callable[[str], Fertilizer | None],
):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def get_fertilizer_by_name(name: str) -> dict:
        """Lookup a fertilizer by name and return JSON with status and record.

        Args:
            name: Fertilizer name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

        Output JSON (success): {"status":"success","fertilizer":{"id","name","usage_sheet","recommended_amount"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        fertilizer = get_fertilizer_by_name_func(name)
        if not fertilizer:
            return {"status": "error", "message": "fertilizer_not_found"}
        return {
            "status": "success",
            "fertilizer": {
                "id": fertilizer.id,
                "name": fertilizer.name,
                "usage_sheet": fertilizer.usage_sheet,
                "recommended_amount": fertilizer.recommended_amount,
                "sources": fertilizer.sources,
            },
        }

    return get_fertilizer_by_name



def _extract_recommended_amount(text: str) -> str:
    match = re.search(
        r"(\d+[\.,]?\d*\s*(ml|g|mg|kg|l|L)\s*/?\s*(l|L|litro|litros|100\s*l)?)",
        text,
    )
    if match:
        return match.group(0)
    return "No disponible"
