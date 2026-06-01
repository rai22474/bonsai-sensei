from typing import Callable

from bonsai_sensei.domain.services.tool_tracer import trace_tool_call


def create_search_phytosanitary_online_tool(searcher: Callable[[str], dict]) -> Callable:
    @trace_tool_call
    def search_phytosanitary_online(pest_name: str, bonsai_name: str | None = None) -> dict:
        """Search online for phytosanitary products suitable for treating a pest on bonsai.

        Use this tool when the user asks for product advice and no products are registered
        in the catalog (i.e. recommend_phytosanitary returned 'no_products_available').

        Args:
            pest_name: Name of the pest to treat (e.g. 'araña roja', 'pulgón', 'oídio').
            bonsai_name: Optional bonsai name for context (helps narrow results by species).

        Returns:
            A JSON-ready dictionary with status 'success' and the search answer, or 'error'.
            Output JSON (success): {"status": "success", "answer": "<recommendations>", "results": [...]}.
            Output JSON (error): {"status": "error", "message": "<reason>"}.
        """
        query = f"insecticida fungicida fitosanitario bonsai {pest_name} tratamiento recomendacion"
        if bonsai_name:
            query += f" {bonsai_name}"
        result = searcher(query)
        return {
            "status": "success",
            "answer": result.get("answer", ""),
            "results": result.get("results", []),
        }

    return search_phytosanitary_online
