from typing import Callable
import re

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_phytosanitary_info_tool(searcher: Callable[[str], dict]):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def fetch_phytosanitary_info(name: str) -> dict:
        """Fetch phytosanitary info and return JSON with usage sheet and recommended amount.

    Output JSON: {"status":"success","phytosanitary":{"name","usage_sheet","recommended_amount","recommended_for","sources"}}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        query = f"{name} bonsai dosis de uso ficha tecnica fitosanitario"
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
            "phytosanitary": {
                "name": name,
                "usage_sheet": usage_sheet,
                "recommended_amount": recommended_amount,
                "recommended_for": "",
                "sources": sources,
            },
        }

    return fetch_phytosanitary_info


def create_create_phytosanitary_tool(
    create_phytosanitary_func: Callable[[Phytosanitary], Phytosanitary],
):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def create_phytosanitary(
        name: str,
        usage_sheet: str,
        recommended_amount: str,
        recommended_for: str,
    ) -> dict:
        """Create a phytosanitary and return JSON with status and record.

    Output JSON (success): {"status":"success","phytosanitary":{"id","name","usage_sheet","recommended_amount","recommended_for"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        if not usage_sheet:
            return {"status": "error", "message": "usage_sheet_required"}
        if not recommended_amount:
            return {"status": "error", "message": "recommended_amount_required"}
        if not recommended_for:
            return {"status": "error", "message": "recommended_for_required"}
        created = create_phytosanitary_func(
            phytosanitary=Phytosanitary(
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                recommended_for=recommended_for,
            )
        )
        return {
            "status": "success",
            "phytosanitary": {
                "id": created.id,
                "name": created.name,
                "usage_sheet": created.usage_sheet,
                "recommended_amount": created.recommended_amount,
                "recommended_for": created.recommended_for,
            },
        }

    return create_phytosanitary


def create_list_phytosanitary_tool(
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def list_phytosanitary() -> dict:
        """Return JSON with all registered phytosanitary items.

    Output JSON: {"status":"success","phytosanitary":[{"id","name","usage_sheet","recommended_amount","recommended_for"}]}.
        """
        items = list_phytosanitary_func()
        results = [
            {
                "id": phytosanitary.id,
                "name": phytosanitary.name,
                "usage_sheet": phytosanitary.usage_sheet,
                "recommended_amount": phytosanitary.recommended_amount,
                "recommended_for": phytosanitary.recommended_for,
            }
            for phytosanitary in items
        ]
        return {"status": "success", "phytosanitary": results}

    return list_phytosanitary


def create_get_phytosanitary_by_name_tool(
    get_phytosanitary_by_name_func: Callable[[str], Phytosanitary | None],
):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def get_phytosanitary_by_name(name: str) -> dict:
        """Lookup a phytosanitary by name and return JSON with status and record.

    Output JSON (success): {"status":"success","phytosanitary":{"id","name","usage_sheet","recommended_amount","recommended_for"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        phytosanitary = get_phytosanitary_by_name_func(name)
        if not phytosanitary:
            return {"status": "error", "message": "phytosanitary_not_found"}
        return {
            "status": "success",
            "phytosanitary": {
                "id": phytosanitary.id,
                "name": phytosanitary.name,
                "usage_sheet": phytosanitary.usage_sheet,
                "recommended_amount": phytosanitary.recommended_amount,
                "recommended_for": phytosanitary.recommended_for,
            },
        }

    return get_phytosanitary_by_name


def _extract_recommended_amount(text: str) -> str:
    match = re.search(
        r"(\d+[\.,]?\d*\s*(ml|g|mg|kg|l|L)\s*/?\s*(l|L|litro|litros|100\s*l)?)",
        text,
    )
    if match:
        return match.group(0)
    return "No disponible"