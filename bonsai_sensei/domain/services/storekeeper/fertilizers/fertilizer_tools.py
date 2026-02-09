from typing import Callable
import re

from bonsai_sensei.domain.fertilizer import Fertilizer
from bonsai_sensei.domain.services.tool_limiter import limit_tool_calls


def create_fertilizer_info_tool(searcher: Callable[[str], dict]):
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


def create_register_fertilizer_tool(
    searcher: Callable[[str], dict],
    create_fertilizer_func: Callable[[Fertilizer], Fertilizer],
):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def register_fertilizer(name: str) -> dict:
        """Register a fertilizer after fetching usage details.

        Args:
            name: Fertilizer name to register.

        Returns:
            A JSON-ready dictionary with the registration result.

        Output JSON (success): {"status":"success","fertilizer":{"id","name","usage_sheet","recommended_amount","sources"}}.
        Output JSON (error): {"status":"error","message": "..."}.
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
        created = create_fertilizer_func(
            fertilizer=Fertilizer(
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                sources=sources,
            )
        )
        return {
            "status": "success",
            "fertilizer": {
                "id": created.id,
                "name": created.name,
                "usage_sheet": created.usage_sheet,
                "recommended_amount": created.recommended_amount,
                "sources": created.sources,
            },
        }

    return register_fertilizer


def create_create_fertilizer_tool(create_fertilizer_func: Callable[[Fertilizer], Fertilizer]):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def create_fertilizer(
        name: str,
        usage_sheet: str,
        recommended_amount: str,
        sources: list[str] | None = None,
    ) -> dict:
        """Create a fertilizer and return JSON with status and record.

        Args:
            name: Fertilizer name.
            usage_sheet: Usage instructions.
            recommended_amount: Recommended dosage.
            sources: Source URLs for the information.

        Returns:
            A JSON-ready dictionary with the creation result.

        Output JSON (success): {"status":"success","fertilizer":{"id","name","usage_sheet","recommended_amount"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        if not usage_sheet:
            return {"status": "error", "message": "usage_sheet_required"}
        if not recommended_amount:
            return {"status": "error", "message": "recommended_amount_required"}
        if sources is None:
            sources = []
        created = create_fertilizer_func(
            fertilizer=Fertilizer(
                name=name,
                usage_sheet=usage_sheet,
                recommended_amount=recommended_amount,
                sources=sources,
            )
        )
        return {
            "status": "success",
            "fertilizer": {
                "id": created.id,
                "name": created.name,
                "usage_sheet": created.usage_sheet,
                "recommended_amount": created.recommended_amount,
                "sources": created.sources,
            },
        }

    return create_fertilizer


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


def create_update_fertilizer_tool(
    update_fertilizer_func: Callable[[str, dict], Fertilizer | None],
):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def update_fertilizer(
        name: str,
        usage_sheet: str | None = None,
        recommended_amount: str | None = None,
        sources: list[str] | None = None,
    ) -> dict:
        """Update a fertilizer and return JSON with status and updated record.

        Args:
            name: Fertilizer name to update.
            usage_sheet: New usage instructions.
            recommended_amount: New recommended dosage.
            sources: New source URLs.

        Returns:
            A JSON-ready dictionary with the update result.

        Output JSON (success): {"status":"success","fertilizer":{"id","name","usage_sheet","recommended_amount","sources"}}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        if usage_sheet is None and recommended_amount is None and sources is None:
            return {"status": "error", "message": "fertilizer_update_required"}
        fertilizer = update_fertilizer_func(
            name,
            {
                "usage_sheet": usage_sheet,
                "recommended_amount": recommended_amount,
                "sources": sources,
            },
        )
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

    return update_fertilizer


def create_delete_fertilizer_tool(delete_fertilizer_func: Callable[[str], bool]):
    @limit_tool_calls(agent_name="fertilizer_storekeeper")
    def delete_fertilizer(name: str) -> dict:
        """Delete a fertilizer by name and return JSON with status.

        Args:
            name: Fertilizer name to delete.

        Returns:
            A JSON-ready dictionary with the deletion result.

        Output JSON (success): {"status":"success","name": "..."}.
        Output JSON (error): {"status":"error","message": "..."}.
        """
        if not name:
            return {"status": "error", "message": "fertilizer_name_required"}
        success = delete_fertilizer_func(name)
        if not success:
            return {"status": "error", "message": "fertilizer_not_found"}
        return {"status": "success", "name": name}

    return delete_fertilizer


def _extract_recommended_amount(text: str) -> str:
    match = re.search(
        r"(\d+[\.,]?\d*\s*(ml|g|mg|kg|l|L)\s*/?\s*(l|L|litro|litros|100\s*l)?)",
        text,
    )
    if match:
        return match.group(0)
    return "No disponible"