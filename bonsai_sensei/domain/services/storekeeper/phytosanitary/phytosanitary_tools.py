from typing import Callable
import re

from bonsai_sensei.domain.phytosanitary import Phytosanitary
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_phytosanitary_info_tool(searcher: Callable[[str], dict]):
    
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def fetch_phytosanitary_info(name: str) -> dict:
        """Fetch phytosanitary info and return JSON with usage sheet and recommended amount.

        Args:
            name: Phytosanitary product name to look up.

        Returns:
            A JSON-ready dictionary with the fetched phytosanitary info.

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
        recommended_for = "Plagas comunes"
        return {
            "status": "success",
            "phytosanitary": {
                "name": name,
                "usage_sheet": usage_sheet,
                "recommended_amount": recommended_amount,
                "recommended_for": recommended_for,
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
        sources: list[str] | None = None,
    ) -> dict:
        """Create a phytosanitary and return JSON with status and record.

        Args:
            name: Phytosanitary name.
            usage_sheet: Usage instructions.
            recommended_amount: Recommended dosage.
            recommended_for: Target pest or disease.
            sources: Source URLs for the information.

        Returns:
            A JSON-ready dictionary with the creation result.

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
        if sources is None:
            sources = []
        created = create_phytosanitary_func(
            phytosanitary=Phytosanitary(
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                recommended_for=recommended_for,
                sources=sources,
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
                "sources": created.sources,
            },
        }

    return create_phytosanitary


def create_list_phytosanitary_tool(
    list_phytosanitary_func: Callable[[], list[Phytosanitary]],
):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def list_phytosanitary() -> dict:
        """Return JSON with all registered phytosanitary items.

        Returns:
            A JSON-ready dictionary with the phytosanitary list.

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
                "sources": phytosanitary.sources,
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

        Args:
            name: Phytosanitary name to look up.

        Returns:
            A JSON-ready dictionary with the lookup result.

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
                "sources": phytosanitary.sources,
            },
        }

    return get_phytosanitary_by_name


def create_update_phytosanitary_tool(
    update_phytosanitary_func: Callable[[str, dict], Phytosanitary | None],
):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def update_phytosanitary(
        name: str,
        usage_sheet: str | None = None,
        recommended_amount: str | None = None,
        recommended_for: str | None = None,
        sources: list[str] | None = None,
    ) -> dict:
        """Update a phytosanitary and return JSON with status and updated record.

        Args:
            name: Phytosanitary name to update.
            usage_sheet: New usage instructions.
            recommended_amount: New recommended dosage.
            recommended_for: New target pest or disease.
            sources: New source URLs.

        Returns:
            A JSON-ready dictionary with the update result.

        Output JSON (success): {"status":"success","phytosanitary":{"id","name","usage_sheet","recommended_amount","recommended_for","sources"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        if (
            usage_sheet is None
            and recommended_amount is None
            and recommended_for is None
            and sources is None
        ):
            return {"status": "error", "message": "phytosanitary_update_required"}
        phytosanitary = update_phytosanitary_func(
            name,
            {
                "usage_sheet": usage_sheet,
                "recommended_amount": recommended_amount,
                "recommended_for": recommended_for,
                "sources": sources,
            },
        )
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
                "sources": phytosanitary.sources,
            },
        }

    return update_phytosanitary


def create_delete_phytosanitary_tool(delete_phytosanitary_func: Callable[[str], bool]):
    @limit_tool_calls(agent_name="phytosanitary_storekeeper")
    def delete_phytosanitary(name: str) -> dict:
        """Delete a phytosanitary by name and return JSON with status.

        Args:
            name: Phytosanitary name to delete.

        Returns:
            A JSON-ready dictionary with the deletion result.

        Output JSON (success): {"status":"success","name": "..."}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "phytosanitary_name_required"}
        success = delete_phytosanitary_func(name)
        if not success:
            return {"status": "error", "message": "phytosanitary_not_found"}
        return {"status": "success", "name": name}

    return delete_phytosanitary


def _extract_recommended_amount(text: str) -> str:
    match = re.search(
        r"(\d+[\.,]?\d*\s*(ml|g|mg|kg|l|L)\s*/?\s*(l|L|litro|litros|100\s*l)?)",
        text,
    )
    if match:
        return match.group(0)
    return "No disponible"