# Stack

## Runtime
- Python 3.12
- FastAPI (REST API)
- uv (dependency management)

## Memory graph
- `graphiti-core` — temporal knowledge graph for episodic memory storage and retrieval

## Database
- PostgreSQL (shared instance with `bonsai_sensei`)

## ADK integration
- `google-adk` — implements `BaseMemoryService` interface
- Consumed by `bonsai_sensei` runner via `memory_service` parameter on `InMemoryRunner`
- `PreloadMemory` built-in tool activates automatically when `MemoryService` is registered

## Observability
- Prometheus metrics (shared with other services via `monitoring/`)
