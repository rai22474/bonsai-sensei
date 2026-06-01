# bonsai_sensei

Main Telegram bot and bonsai domain service. Handles all user-facing interactions, domain data management, and the conversational AI pipeline.

## Responsibilities

- Telegram bot for end users (messages, photos, inline keyboards, polls)
- Bonsai collection, species registry, fertilizers, phytosanitary, cultivation plans
- Multi-agent AI pipeline (sensei → mitori → shokunin → sub-agents)
- Episodic memory via Honcho (conversational context across sessions)
- Wiki knowledge search via HTTP to `knowledge_base`

## Agent architecture

```
sensei                          [orchestrator]
├── [query tools]               Direct read-only tools
└── command_pipeline            SequentialAgent for write operations
    ├── mitori                  Planner: produces a JSON action plan
    └── shokunin                Deterministic executor (no LLM)
        ├── analyze_bonsai_photo
        ├── compare_bonsai_photos
        ├── get_weather_risk
        ├── recommend_fertilizer
        ├── botanist            Species registry + wiki generation
        ├── kikaru              Cultivation planning
        ├── nursery             Bonsai CRUD
        ├── caretaker           Event recording
        ├── gallery             Photo management
        └── storekeeper         Fertilizer & phytosanitary catalogues
```

| Agent | Japanese | Role |
|---|---|---|
| sensei | 先生 | Entry point, routes queries and commands |
| mitori | 見取り | Planner, produces typed JSON action plan |
| shokunin | 職人 | Deterministic executor |
| kikaru | 木刈る | Cultivation work calendar |

## Setup

```bash
cd bonsai_sensei
uv sync
uv run uvicorn bonsai_sensei.main:app --reload
```

Runs database migrations on startup via `alembic upgrade head`.

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | Main bot token |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_MODEL` | Leaf agent model (default: `gemini-2.0-flash-lite`) |
| `GEMINI_ORCHESTRATOR_MODEL` | Orchestrator model |
| `MODEL_PROVIDER` | `cloud` or `local` (default: `cloud`) |
| `KB_BASE_URL` | knowledge_base service URL (default: `http://knowledge_base:8080`) |
| `PHOTOS_PATH` | Photo storage directory (default: `./photos`) |
| `TAVILY_API_KEY` | Web search for wiki content generation |
| `HONCHO_API_KEY` | Honcho API key for episodic memory |
| `HONCHO_WORKSPACE_ID` | Honcho workspace ID (default: `bonsai-sensei`) |
| `HONCHO_BASE_URL` | Honcho base URL (optional, for self-hosted) |
| `ADMIN_TELEGRAM_BOT_TOKEN` | Admin bot token |
| `ADMIN_TELEGRAM_CHAT_ID` | Admin chat ID |

## Tests

```bash
cd bonsai_sensei
pytest tests/unit/
pytest tests/integration/ -m integration
pytest tests/acceptance/   # requires running stack
```

## API

Swagger UI available at `http://localhost:8050/docs` when running locally.

Key endpoint groups: `/api/bonsai`, `/api/species`, `/api/fertilizers`, `/api/phytosanitary`, `/api/advice`, `/api/planned_works`, `/api/pests`.
