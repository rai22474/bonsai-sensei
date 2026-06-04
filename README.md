# Bonsai Sensei

AI-powered bonsai care system operated via Telegram. Two application services, one observability stack.

## Architecture

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│         bonsai_sensei           │     │          knowledge_base           │
│                                 │     │                                   │
│  Telegram bot (main user bot)   │     │  Wiki pipeline + admin bot        │
│  Bonsai domain (CRUD, plans)    │────►│  Dreamer, ingestion, wiki index   │
│  Conversational AI (ADK)        │     │  Episodic memory → wiki           │
│  PostgreSQL (domain data)       │     │  Filesystem (wiki, transcripts)   │
└─────────────────────────────────┘     └──────────────────────────────────┘
         │                                          │
         └──────────────┬───────────────────────────┘
                        ▼
         ┌──────────────────────────────────┐
         │         Observability stack       │
         │                                  │
         │  Honcho   — episodic memory      │
         │  Jaeger   — distributed traces   │
         │  Prometheus — metrics scraping   │
         │  Grafana  — dashboards           │
         └──────────────────────────────────┘
```

## Services

| Service | Port | Description |
|---|---|---|
| `bonsai_sensei` | 8050 | Main bot + domain |
| `knowledge_base` | 8051 | Wiki pipeline + admin bot |
| `honcho-api` | 8000 | Episodic memory (Honcho) |
| `jaeger` | 9686 | Distributed tracing UI |
| `prometheus` | 9090 | Metrics |
| `grafana` | 3000 | Dashboards |

Detailed README per service: [bonsai_sensei/README.md](bonsai_sensei/README.md) · [knowledge_base/README.md](knowledge_base/README.md)

## Observability

**Honcho** stores per-user episodic memory across conversations. The sensei reads and writes memories via Honcho API; the knowledge_base dreamer synthesises memories into wiki pages.

**Jaeger** receives OpenTelemetry traces from both services (OTLP/gRPC on port 4317). Every ADK tool call and MCP request is instrumented. UI at `http://localhost:9686`.

**Prometheus + Grafana** collect LLM and MCP request metrics (count, latency, status). The `bonsai_sensei` Grafana dashboard shows per-tool call rates and p50/p95 latencies. UI at `http://localhost:3000`.

## Run

```bash
docker compose up
```

Requires a `.env` file at project root. See each service README for required variables.

## Repository structure

```
bonsai_sensei/        ← main bot service (domain + AI pipeline)
  src/bonsai_sensei/
  tests/
  pyproject.toml
  Dockerfile

knowledge_base/       ← wiki service (pipeline + admin bot)
  src/knowledge_base/
  tests/
  pyproject.toml
  Dockerfile

monitoring/
  grafana/            ← dashboard provisioning
  prometheus.yml      ← scrape config

docker-compose.yml
docs/                 ← architecture decisions, vision, technical debt
scripts/
```
