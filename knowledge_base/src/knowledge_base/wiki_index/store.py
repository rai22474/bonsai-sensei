from typing import Callable

import falkordb
from redis.exceptions import ResponseError

from knowledge_base.wiki_index.embedder import EMBEDDING_DIM
from knowledge_base.wiki_index.entry import IndexEntry


def initialize_schema(graph: falkordb.Graph) -> None:
    """Create WikiPage vector index, migrating data if embedding dimensions changed."""
    try:
        graph.create_node_vector_index('WikiPage', 'embedding', dim=EMBEDDING_DIM, similarity_function='cosine')
    except ResponseError as error:
        if 'already indexed' not in str(error).lower():
            raise
        _migrate_index_if_dim_changed(graph)


def _migrate_index_if_dim_changed(graph: falkordb.Graph) -> None:
    result = graph.query(
        "MATCH (n:WikiPage) WHERE n.embedding IS NOT NULL RETURN n.embedding LIMIT 1"
    )
    if not result.result_set:
        return
    existing_embedding = result.result_set[0][0]
    if existing_embedding and len(existing_embedding) == EMBEDDING_DIM:
        return
    graph.query("MATCH (n:WikiPage) DETACH DELETE n")
    try:
        graph.query("DROP INDEX ON :WikiPage(embedding)")
    except Exception:
        pass
    graph.create_node_vector_index('WikiPage', 'embedding', dim=EMBEDDING_DIM, similarity_function='cosine')


def create_save_entry(graph: falkordb.Graph) -> Callable[[IndexEntry], None]:
    """Return a callable that persists an IndexEntry to FalkorDB."""
    def save_entry(entry: IndexEntry) -> None:
        graph.query(
            "MERGE (node:WikiPage {page_path: $page_path}) "
            "SET node.abstract = $abstract, node.embedding = vecf32($embedding)",
            {'page_path': entry.page_path, 'abstract': entry.abstract, 'embedding': entry.embedding},
        )
        for link in entry.links:
            graph.query(
                "MATCH (source:WikiPage {page_path: $source_path}) "
                "MERGE (target:WikiPage {page_path: $target_path}) "
                "MERGE (source)-[:LINKS_TO]->(target)",
                {'source_path': entry.page_path, 'target_path': link},
            )
    return save_entry


def create_load_entry(graph: falkordb.Graph) -> Callable[[str], IndexEntry | None]:
    """Return a callable that loads a single IndexEntry by page_path."""
    def load_entry(page_path: str) -> IndexEntry | None:
        result = graph.query(
            "MATCH (node:WikiPage {page_path: $page_path}) RETURN node",
            {'page_path': page_path},
        )
        if not result.result_set:
            return None
        node = result.result_set[0][0]
        return IndexEntry(
            page_path=node.properties['page_path'],
            abstract=node.properties.get('abstract', ''),
            links=_load_links(graph, page_path),
            embedding=list(node.properties.get('embedding', [])),
        )
    return load_entry


def create_load_all_entries(graph: falkordb.Graph) -> Callable[[], list[IndexEntry]]:
    """Return a callable that loads all IndexEntry records from FalkorDB."""
    def load_all_entries() -> list[IndexEntry]:
        result = graph.query("MATCH (node:WikiPage) WHERE node.abstract IS NOT NULL RETURN node")
        return [
            IndexEntry(
                page_path=node.properties['page_path'],
                abstract=node.properties.get('abstract', ''),
                links=_load_links(graph, node.properties['page_path']),
                embedding=list(node.properties.get('embedding', [])),
            )
            for row in result.result_set
            for node in [row[0]]
        ]
    return load_all_entries


def _load_links(graph: falkordb.Graph, page_path: str) -> list[str]:
    result = graph.query(
        "MATCH (:WikiPage {page_path: $page_path})-[:LINKS_TO]->(target:WikiPage) RETURN target.page_path",
        {'page_path': page_path},
    )
    return [row[0] for row in result.result_set]
