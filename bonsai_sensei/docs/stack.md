# Stack

## Runtime
- Python 3.12
- FastAPI (REST API + webhook endpoints)
- uv (dependency management)

## Agent framework
- Google ADK (`google-adk`) — agent orchestration, session management, tool dispatch
- Agent hierarchy: sensei (root) → mitori → shokunin → [kikaru, kantei, sakuteiki, storekeeper]
- Pipeline agents (mitori/shokunin) for structured commands; free agents for conversational flows

## LLM
- Gemini via `google-genai`
- Model configured via `GEMINI_MODEL` env var
- Orchestrator uses a more capable model; sub-agents use lighter models where appropriate

## Database
- PostgreSQL with Alembic migrations
- pgvector extension for wiki embeddings index
- SQLAlchemy ORM

## Telegram
- `python-telegram-bot` — bot API, inline keyboards, confirmation callbacks
- Webhook-based (not polling)
- Admin channel via `ADMIN_TELEGRAM_CHAT_ID` for wiki review (FUTURE-001)

## Memory
- ADK `InMemorySession` for intra-session state
- `episodic_memory` service (Graphiti) for cross-session persistence
- `wiki_index/` for semantic wiki search (gemini-embedding-001, 3072 dims)

## Observability
- Prometheus metrics (shared with other services via `monitoring/`)
- Grafana dashboards
