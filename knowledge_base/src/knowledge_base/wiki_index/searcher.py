from typing import Callable

import falkordb


def create_search_by_embedding(graph: falkordb.Graph) -> Callable[[list[float], int], list[tuple[str, str, float]]]:
    """Return a callable that performs KNN vector search over WikiPage nodes."""
    def search_by_embedding(query_embedding: list[float], top_k: int = 5) -> list[tuple[str, str, float]]:
        """Return top_k (page_path, abstract, score) tuples sorted by cosine similarity descending."""
        result = graph.query(
            "CALL db.idx.vector.queryNodes('WikiPage', 'embedding', $k, vecf32($embedding)) "
            "YIELD node, score "
            "RETURN node.page_path, node.abstract, score",
            {'k': top_k, 'embedding': query_embedding},
        )
        return [
            (row[0], row[1], round(1.0 - row[2], 6))
            for row in result.result_set
            if row[0] is not None and row[1] is not None
        ]
    return search_by_embedding
