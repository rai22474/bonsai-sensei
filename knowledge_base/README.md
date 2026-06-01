# knowledge_base

Wiki pipeline service. Builds and maintains a Markdown wiki from YouTube transcripts and episodic observations captured in user conversations. Exposes the wiki via REST API.

## Responsibilities

- Admin Telegram bot (ingestion triggers, wiki review, dreamer control)
- Transcript ingestion pipeline (YouTube → knowledge cards → wiki)
- Wiki dreamer: autonomous agent that maintains wiki coherence
- Wiki editor: admin-triggered wiki editing agent
- Semantic wiki index (embeddings for search)
- Episodic memory → wiki (observations submitted by `bonsai_sensei`)
- Git-backed wiki with commit history and review flow

## Components

```
ingestion/          YouTube transcript → knowledge card → wiki
dreamer/            Autonomous agent: cards + observations → wiki pages
wiki_editor/        Admin-triggered wiki editing via ADK agent
wiki_index/         Embedding-based semantic search index
wiki_git.py         Git operations on the wiki filesystem
api/                REST endpoints (wiki CRUD, search, transcripts, review)
telegram/           Admin bot + wiki review callbacks
```

## Episodic memory flow

```
bonsai_sensei  ──Honcho sessions/conclusions──►  Honcho workspace
                                                        │
                                               dreamer reads on run
                                                        │
                                               wiki pages updated
```

## Setup

```bash
cd knowledge_base
uv sync
uv run uvicorn knowledge_base.main:app --reload
```

Requires a wiki directory (git-initialised on first run).

## Environment variables

| Variable | Description |
|---|---|
| `WIKI_PATH` | Wiki filesystem root (default: `./wiki`) |
| `TRANSCRIPTS_PATH` | Transcripts directory (default: `./transcripts`) |
| `GEMINI_API_KEY` | Gemini API key (embeddings + dreamer model) |
| `GEMINI_MODEL` | Model for dreamer/editor agents |
| `GEMINI_ORCHESTRATOR_MODEL` | Orchestrator model |
| `ADMIN_TELEGRAM_BOT_TOKEN` | Admin bot token |
| `ADMIN_TELEGRAM_CHAT_ID` | Admin chat ID |
| `WIKI_DREAMER_INTERVAL_SECONDS` | Dreamer scheduler interval (default: 1800) |
| `HONCHO_API_KEY` | Honcho API key (dreamer reads observations) |
| `HONCHO_WORKSPACE_ID` | Honcho workspace ID (default: `bonsai-sensei`) |

## Tests

```bash
cd knowledge_base
pytest tests/unit/
pytest tests/acceptance/   # requires running stack
```

## API

Key endpoint groups:

| Endpoint | Description |
|---|---|
| `GET/PUT/DELETE /api/wiki` | Wiki page CRUD |
| `GET /api/wiki/files` | List wiki files |
| `POST /api/wiki/index/search` | Semantic wiki search |
| `POST /api/wiki/index/rebuild` | Rebuild full embedding index |
| `POST /api/wiki/transcripts/ingest` | Trigger YouTube ingestion |
| `POST /api/wiki/transcripts/wiki-dreamer/run/sync` | Run dreamer synchronously |
| `GET /api/wiki/review/sessions` | List active review sessions |
