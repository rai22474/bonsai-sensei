# Bonsai Sensei

An intelligent conversational assistant for bonsai care, operated via Telegram.

## Features

- **Bonsai Collection**: Create, update, delete and list bonsais. Receive photos via Telegram and associate them to a bonsai.
- **Species Registry**: Register species with automatic scientific name resolution (Trefle API) and care guides generated and stored as Markdown wiki pages.
- **Fertilizer Catalogue**: Track fertilizers with wiki pages containing dosage and application details.
- **Phytosanitary Catalogue**: Track phytosanitary products with wiki pages and recommended dosages.
- **Cultivation Planning**: Schedule fertilizations, phytosanitary treatments and transplants with automatic date suggestions.
- **Event Recording**: Log completed care events (fertilizations applied, treatments, transplants, planned work execution).
- **Weather Advice**: Fetch forecasts and advise on frost or heat protection for specific species.
- **Photo Management**: Receive bonsai photos via Telegram, view the latest or historical photos per bonsai.
- **Guided Confirmations**: All write operations require explicit user confirmation via Telegram inline buttons. Cancellations can include a reason.
- **Selection flows**: When multiple options exist (e.g. ambiguous scientific names), an inline keyboard is shown for the user to choose.
- **Wiki Knowledge Base**: Care guides, fertilizer sheets and phytosanitary data live as Markdown files compatible with Obsidian.
- **REST API**: FastAPI endpoints for all resources — bonsai, species, fertilizers, phytosanitary, events, photos, advice and wiki.

## Agent Architecture

The system uses a CQRS pattern at the agent level: **read queries** are handled directly by sensei with lightweight tool calls, while **write commands** go through a planning and execution pipeline.

```
sensei                        [orchestrator model]
├── [query tools]             Direct read-only tools (no LLM hop)
│   ├── list_bonsai
│   ├── get_bonsai_by_name
│   ├── list_bonsai_events
│   ├── list_bonsai_photos
│   ├── list_species
│   ├── list_fertilizers
│   ├── get_fertilizer_by_name
│   ├── list_phytosanitary
│   ├── get_phytosanitary_by_name
│   └── list_planned_works_for_bonsai
│
└── command_pipeline          SequentialAgent for write operations
    ├── mitori                Planner [orchestrator model]: analyses the request and produces a JSON action plan
    └── shokunin              Executor [leaf model]: runs the plan step by step using the agents below
        ├── botanist          Species registry (CRUD + wiki generation) [leaf model]
        ├── weather_advisor   Climate risk assessment [leaf model]
        ├── kikaru            Cultivation plan [leaf model]: recommends, plans and schedules work
        ├── nursery           Bonsai CRUD + wiki page per species [leaf model]
        ├── caretaker         Event recording: fertilizations, treatments, transplants, planned work [leaf model]
        ├── gallery           Photo management: add, list, delete bonsai photos [leaf model]
        ├── kantei            Visual analysis: analyze and compare bonsai photos, write reports [leaf model]
        └── storekeeper       Fertilizer & phytosanitary catalogues (CRUD + wiki generation) [leaf model]
```

### Agent naming

Agents with domain-specific complexity are named after Japanese bonsai craft concepts:

| Name | Japanese | Meaning | Why |
|---|---|---|---|
| **sensei** | 先生 | teacher / master | The wise entry point that guides the user |
| **mitori** | 見取り | sketch / observe structure | Observes the request and drafts a structural plan before acting |
| **shokunin** | 職人 | craftsman | Executes the plan with precision, step by step |
| **kikaru** | 木刈る | to prune trees | Manages the cultivation work calendar — recommends, plans and schedules care work |

Domain-facing agents (botanist, nursery, caretaker, gallery, kantei, storekeeper, weather_advisor) use descriptive English names that make their responsibility self-evident.

### Models

The system supports a dual-model setup via environment variables:

| Variable | Role | Default |
|---|---|---|
| `GEMINI_MODEL` | Leaf agents (botanist, weather_advisor, kikaru, nursery, caretaker, gallery, kantei, storekeeper) | `gemini-2.0-flash-lite` |
| `GEMINI_ORCHESTRATOR_MODEL` | Orchestrators (sensei, mitori) | falls back to `GEMINI_MODEL` |

### Roles

| Agent | Role |
|---|---|
| **sensei** | Entry point. Routes queries to direct tools, commands to `command_pipeline`. Formats responses for Telegram. |
| **mitori** | Planner. Reads the request and the available agent descriptions, then outputs a self-audited JSON action plan. |
| **shokunin** | Executor. Runs each step of mitori's plan, delegating to the appropriate leaf agent. Stops immediately on `confirmation_pending`. |
| **botanist** | Manages the species registry (CRUD). Resolves scientific names via Trefle and generates wiki care guides via Tavily at confirmation time. |
| **weather_advisor** | Fetches weather forecasts and advises on frost/heat protection for specific species. |
| **kikaru** | Manages the cultivation work calendar (fertilizations, transplants, treatments). Uses deterministic recommendation tools that gather context, reason, and persist the plan to the wiki in a single guaranteed step. Applies next-Saturday default when the user specifies no date. |
| **nursery** | Manages the bonsai collection (CRUD). Creates wiki pages per species at confirmation time. |
| **caretaker** | Records completed care events: fertilizations applied, phytosanitary treatments, transplants, and planned work execution. |
| **gallery** | Manages bonsai photos: receives photos from Telegram, associates them to a bonsai, lists and deletes them. |
| **kantei** | Visual analysis of bonsai photos. Analyzes individual photos, compares two photos over time, and writes structured reports to the wiki. |
| **storekeeper** | Manages the fertilizer and phytosanitary catalogues (CRUD + wiki page generation via Tavily). |

### Tools

| Agent | Tools |
|---|---|
| **sensei** | `list_bonsai`, `get_bonsai_by_name`, `list_bonsai_events`, `list_bonsai_photos`, `list_species`, `list_fertilizers`, `get_fertilizer_by_name`, `list_phytosanitary`, `get_phytosanitary_by_name`, `list_planned_works_for_bonsai`, `command_pipeline` |
| **mitori** | — |
| **shokunin** | `botanist`, `weather_advisor`, `kikaru`, `nursery`, `caretaker`, `gallery`, `kantei`, `storekeeper` |
| **botanist** | `confirm_create_species`, `confirm_update_species`, `confirm_delete_species`, `confirm_refresh_species_wiki` |
| **weather_advisor** | `get_weather`, `list_bonsai_species` |
| **kikaru** | `recommend_fertilizer`, `recommend_phytosanitary`, `list_planned_works_for_bonsai`, `list_bonsai_events_for_cultivation`, `confirm_create_fertilizer_application`, `confirm_create_phytosanitary_application`, `confirm_create_transplant`, `confirm_delete_planned_work`, `list_bonsai`, `list_weekend_planned_works` |
| **nursery** | `list_bonsai`, `get_bonsai_by_name`, `confirm_create_bonsai`, `confirm_update_bonsai`, `confirm_delete_bonsai` |
| **caretaker** | `apply_fertilizer`, `apply_phytosanitary`, `record_transplant`, `list_bonsai_events`, `list_planned_works_for_bonsai`, `execute_planned_work` |
| **gallery** | `add_bonsai_photo`, `list_bonsai_photos`, `delete_bonsai_photo` |
| **kantei** | `analyze_bonsai_photo`, `compare_bonsai_photos`, `write_wiki_page`, `update_bonsai_reports_index` |
| **storekeeper** | `list_fertilizers`, `confirm_create_fertilizer`, `confirm_update_fertilizer`, `confirm_delete_fertilizer`, `confirm_refresh_fertilizer_wiki`, `list_phytosanitary`, `confirm_create_phytosanitary`, `confirm_update_phytosanitary`, `confirm_delete_phytosanitary`, `confirm_refresh_phytosanitary_wiki` |

### Confirmation flow

Write operations that mutate data require explicit user confirmation. The leaf agent calls a `confirm_*` tool which queues the operation and returns `confirmation_pending`. Shokunin stops execution and sensei surfaces the pending confirmation to the user as a Telegram inline button. The operation executes only after the user taps "Accept". Cancellations can optionally include a free-text reason.

### Selection flow

When a command is ambiguous (e.g. multiple scientific names found for a species), the agent calls `ask_selection` which sends an inline keyboard to the user. Execution resumes once the user picks an option or cancels.

### Photo flow

When the user sends a photo in Telegram, the bot uploads it and sends `gallery` a `[FOTO RECIBIDA: <path>]` marker. Gallery shows an inline keyboard with the available bonsais for the user to pick. After confirmation, the photo is stored under `photos/{bonsai_name}/` and associated to the bonsai in the database. Photos are returned via `list_bonsai_photos` and delivered back to the user as Telegram photos.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker (for the full stack including Jaeger and PostgreSQL)
- Ollama (optional, for local model mode)

## Installation

1. Clone the repository.
2. Install dependencies:

    ```bash
    uv sync
    ```

## Running Locally

Run the server with:

```bash
uv run uvicorn bonsai_sensei.main:app --reload
```

Open http://127.0.0.1:8000/docs to see the Swagger UI.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `MODEL_PROVIDER` | `cloud` (Gemini) or `local` (Ollama) | `cloud` |
| `GEMINI_MODEL` | Gemini model for leaf agents | `gemini-2.0-flash-lite` |
| `GEMINI_ORCHESTRATOR_MODEL` | Gemini model for orchestrators | falls back to `GEMINI_MODEL` |
| `OLLAMA_API_BASE` | Ollama server URL | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5:32b-instruct` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — |
| `TREFLE_API_TOKEN` | Trefle API token for scientific name resolution | — |
| `TREFLE_API_BASE` | Trefle API base URL | `https://trefle.io` |
| `TAVILY_API_KEY` | Tavily API key for wiki content generation | — |
| `WIKI_PATH` | Path to the wiki directory (Markdown files) | `./wiki` |
| `PHOTOS_PATH` | Path to the photos directory | `./photos` |

## Acceptance Tests (BDD)

Run the BDD acceptance test suite:

```bash
./acceptance-tests/run_bdd_acceptance.sh
```

Run a specific suite:

```bash
./acceptance-tests/run_bdd_acceptance.sh acceptance-tests/manage_bonsai_photos
```

The acceptance tests spin up a Docker stack with the application, PostgreSQL and stubbed external services.

## Observability

The system uses **OpenTelemetry** for distributed tracing and metrics. The production `docker-compose.yml` includes a **Jaeger** instance for trace visualisation.

### Traces

Every agent execution emits an `agent.run` span. Every tool call emits a `tool.call.<name>` child span. HTTP calls made via `httpx` are auto-instrumented.

| Span | Key attributes |
|---|---|
| `agent.run` | `session.id`, `agent.name`, `model.max_llm_calls`, `agent.event_count` |
| `tool.call.*` | span name encodes the tool name |

Set `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true` to include LLM message content in ADK-generated spans.

### Metrics

| Metric | Type | Tags | Description |
|---|---|---|---|
| `telegram.message.count` | Counter | `user.id` | Telegram messages processed |
| `telegram.message.latency` | Histogram (ms) | `user.id` | End-to-end Telegram message latency |
| `agent.execution.count` | Counter | `user.id` | Agent pipeline executions |
| `agent.execution.latency` | Histogram (ms) | `user.id` | Agent pipeline execution latency |

### Configuration

| Variable | Description | Default |
|---|---|---|
| `OBSERVABILITY_ENABLED` | Set to `false` to disable all telemetry | `true` |
| `OTEL_SERVICE_NAME` | Service name reported in traces | `bonsai-sensei` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC endpoint | `http://jaeger:4317` |
| `OTEL_TRACES_FILE` | Write spans as JSONL to this file instead of OTLP | — |
| `DEPLOYMENT_ENV` | Environment tag on all spans | `production` |
| `SERVICE_VERSION` | Version tag on all spans | `unknown` |

Jaeger UI is available at http://localhost:16686 when running the Docker stack.

## Docker

### Local model (Ollama)

Start Ollama and pull the model if needed:

```bash
./scripts/start_ollama.sh
```

By default this pulls `qwen2.5:32b-instruct`. Override by passing another model name.

Start the stack:

```bash
./scripts/start_applications.sh local
```

### Cloud model (Gemini)

```bash
./scripts/start_applications.sh cloud
```

The stack includes the application, PostgreSQL and Jaeger. Wiki files and photos are mounted as Docker volumes (`./wiki` and `./photos`).
