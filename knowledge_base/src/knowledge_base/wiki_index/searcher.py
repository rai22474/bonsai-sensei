from typing import Callable

import falkordb


def create_search_by_embedding(graph: falkordb.Graph) -> Callable[[list[float], int, str | None], list[tuple[str, str, float]]]:
    """Return a callable that performs KNN vector search over WikiPage nodes.

    When user_id is None, returns only global pages (user_id IS NULL).
    When user_id is provided, returns global pages plus that user's pages.
    """
    def search_by_embedding(query_embedding: list[float], top_k: int = 5, user_id: str | None = None) -> list[tuple[str, str, float]]:
        """Return top_k (page_path, abstract, score) tuples sorted by cosine similarity descending."""
        if user_id is not None:
            cypher = (
                "CALL db.idx.vector.queryNodes('WikiPage', 'embedding', $k, vecf32($embedding)) "
                "YIELD node, score "
                "WHERE node.user_id IS NULL OR node.user_id = $user_id "
                "RETURN node.page_path, node.abstract, score"
            )
            params = {'k': top_k, 'embedding': query_embedding, 'user_id': user_id}
        else:
            cypher = (
                "CALL db.idx.vector.queryNodes('WikiPage', 'embedding', $k, vecf32($embedding)) "
                "YIELD node, score "
                "WHERE node.user_id IS NULL "
                "RETURN node.page_path, node.abstract, score"
            )
            params = {'k': top_k, 'embedding': query_embedding}
        result = graph.query(cypher, params)
        return [
            (row[0], row[1], round(1.0 - row[2], 6))
            for row in result.result_set
            if row[0] is not None and row[1] is not None
        ]
    return search_by_embedding
