# Stack

## Runtime
- Python 3.12
- FastAPI (REST API)
- uv (dependency management)

## Agent framework
- Google ADK (`google-adk`) — keeper agent, wiki editor agent, wiki review session

## LLM
- Gemini via `google-genai`
- Orchestrator (dreamer): `gemini-3-flash-preview` via `GEMINI_ORCHESTRATOR_MODEL` env var, `_MAX_LLM_CALLS=100`
- Auxiliary agents (cleaner, extractor, channel_page_writer): `gemini-3.1-flash-lite-preview`

## Embeddings
- `gemini-embedding-001` (3072 dims) for wiki semantic index
- Index stored at `wiki-index/` (gitignored, treated as regenerable cache)
- Rebuild endpoint: `POST /api/wiki/index/rebuild`

## Wiki storage
- Git-managed directory (`WIKI_PATH` env var)
- `gitpython` for commit/revert operations
- Pages in markdown, one page per concept

## Ingestion
- `youtube-transcript-api` for transcript download

## MCP
- Custom MCP server exposing wiki read/search to external agents

## Observability
- Prometheus metrics (shared with other services via `monitoring/`)
