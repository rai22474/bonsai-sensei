import re
from datetime import date
from typing import Callable

from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_recommend_phytosanitary_tool(
    get_bonsai_by_name_func: Callable,
    list_bonsai_events_func: Callable,
    list_phytosanitary_func: Callable,
    read_wiki_page_func: Callable,
    write_wiki_page_func: Callable,
    run_recommendation: Callable,
) -> Callable:
    @trace_tool_call
    async def recommend_phytosanitary(
        bonsai_name: str,
    ) -> dict:
        """Recommend a complete phytosanitary protection plan for a bonsai based on its history, existing plan, and available products. Saves the plan and rationale in the bonsai's wiki.

        Args:
            bonsai_name: Name of the bonsai to build the phytosanitary plan for.

        Returns:
            A JSON-ready dictionary with status 'success' and the list of treatments, or 'error'.
            Output JSON (success): {"status": "success", "treatments": [{"phytosanitary_name": "...", "purpose": "..."}], "reasoning": "..."}.
            Output JSON (error): {"status": "error", "message": "bonsai_not_found" | "no_products_available"}.
        """
        bonsai = get_bonsai_by_name_func(bonsai_name)
        if not bonsai:
            return {"status": "error", "message": "bonsai_not_found"}

        products = list_phytosanitary_func()
        if not products:
            return {"status": "error", "message": "no_products_available"}

        events = list_bonsai_events_func(bonsai.id) or []

        plan_path = _build_plan_path(bonsai_name)
        existing_plan_result = read_wiki_page_func(path=plan_path)
        existing_plan = existing_plan_result.get("content", "") if existing_plan_result.get("status") == "success" else ""

        product_pages = {}
        for product in products:
            if product.wiki_path:
                page_result = read_wiki_page_func(path=product.wiki_path)
                if page_result.get("status") == "success":
                    product_pages[product.name] = page_result["content"]

        context = _build_context(bonsai_name, date.today().isoformat(), events, existing_plan, products, product_pages)
        recommendation = await run_recommendation(context)

        write_wiki_page_func(path=plan_path, content=recommendation["wiki_content"])

        return {
            "status": "success",
            "treatments": recommendation["treatments"],
            "reasoning": recommendation["reasoning"],
        }

    return recommend_phytosanitary


def _build_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _build_plan_path(bonsai_name: str) -> str:
    return f"bonsai/{_build_slug(bonsai_name)}/phytosanitary-plan.md"


def _build_context(bonsai_name: str, current_date: str, events: list, existing_plan: str, products: list, product_pages: dict) -> str:
    lines = [f"## Bonsái: {bonsai_name}\n", f"Fecha actual: {current_date}\n"]

    if events:
        lines.append("### Historial de eventos de cultivo")
        for event in events:
            lines.append(f"- {event}")
        lines.append("")

    if existing_plan:
        lines.append("### Plan fitosanitario existente en la wiki")
        lines.append(existing_plan)
        lines.append("")

    lines.append("### Productos fitosanitarios disponibles en el catálogo")
    for product in products:
        lines.append(f"- {product.name}")
    lines.append("")

    if product_pages:
        lines.append("### Fichas técnicas de productos")
        for name, content in product_pages.items():
            lines.append(f"#### {name}")
            lines.append(content)
            lines.append("")

    return "\n".join(lines)
