# Bonsai Sensei

AI-powered bonsai care system operated via Telegram. Two independent services.

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│         bonsai_sensei           │     │          knowledge_base           │
│                                 │     │                                   │
│  Telegram bot (main user bot)   │     │  Wiki pipeline + admin bot        │
│  Bonsai domain (CRUD, plans)    │────►│  Dreamer, ingestion, wiki index   │
│  Conversational AI (ADK)        │     │  Episodic memory → wiki           │
│  PostgreSQL (domain data)       │     │  Filesystem (wiki, transcripts)   │
└─────────────────────────────────┘     └──────────────────────────────────┘
```

## Services

| Service | Port | README |
|---|---|---|
| `bonsai_sensei` | 8050 | [bonsai_sensei/README.md](bonsai_sensei/README.md) |
| `knowledge_base` | 8051 | [knowledge_base/README.md](knowledge_base/README.md) |

## Run

```bash
docker compose up
```

Requires a `.env` file at project root. See each service README for required variables.

## Repository structure

```
bonsai_sensei/        ← sensei service (bot + domain)
  src/bonsai_sensei/
  tests/
  pyproject.toml
  Dockerfile

knowledge_base/       ← wiki service (pipeline + admin bot)
  src/knowledge_base/
  tests/
  pyproject.toml
  Dockerfile

docker-compose.yml
docs/
scripts/
```
