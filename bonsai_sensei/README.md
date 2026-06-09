# bonsai_sensei

Main Telegram bot and bonsai domain service. Handles all user-facing interactions, domain data management, and the conversational AI pipeline.

## Responsibilities

- Telegram bot for end users (messages, photos, inline keyboards, polls)
- Bonsai collection, species registry, fertilizers, phytosanitary, cultivation plans
- Multi-agent AI pipeline (sensei → mitori → shokunin → sub-agents)
- Mimamori: daily morning reflection agent (cross-domain, ephemeral, episodic memory read)
- Episodic memory via Graphiti (conversational context across sessions)
- Wiki knowledge search via HTTP to `knowledge_base`

## Agent architecture

### Conversational pipeline (user-triggered)

```
sensei                          [orchestrator, persistent session]
├── [query tools]               Direct read-only tools (wiki, bonsai, events, plans…)
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

### Mimamori (scheduled, independent)

```
mimamori                        [ephemeral InMemoryRunner, runs at 08:00]
├── reads episodic memory       PreloadMemory per user (read-only, no write-back)
├── search_wiki_knowledge       Species care, seasonal windows
├── read_wiki_page              Specific wiki pages
└── list_bonsai_events          Detailed bonsai history
```

Mimamori is fully decoupled from the sensei pipeline. It receives pre-built context (bonsai snapshots, overdue/upcoming works, desalignment flags) via injected callables and sends a Telegram message per user.

| Agent | Japanese | Role |
|---|---|---|
| sensei | 先生 | Entry point, routes queries and commands |
| mitori | 見取り | Planner, produces typed JSON action plan |
| shokunin | 職人 | Deterministic executor |
| kikaru | 木刈る | Cultivation work calendar |
| mimamori | 見守り | Daily guardian, morning reflection |

## Telegram commands

Direct commands bypass the AI sensei — no LLM overhead, instant response.

### Consultas
| Comando | Descripción |
|---|---|
| `/mis_bonsais` | Lista todos los bonsáis |
| `/plan <bonsai>` | Trabajos planificados de un bonsái |
| `/proximos` | Próximos trabajos (14 días) |
| `/fin_de_semana` | Trabajos del próximo sábado y domingo |
| `/historial <bonsai>` | Últimos 20 eventos de un bonsái |
| `/fertilizantes` | Catálogo de fertilizantes |
| `/fitosanitarios` | Catálogo de fitosanitarios |
| `/especies` | Catálogo de especies |
| `/plagas` | Catálogo de plagas |
| `/tiempo [ubicacion]` | Tiempo actual (usa ubicación guardada si se omite) |

Todo lo que modifica datos (crear bonsáis, registrar eventos, aplicar fertilizantes, etc.) va por el sensei conversacional.

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
| `EPISODIC_MEMORY_URL` | Episodic memory service URL (optional; disables memory if unset) |
| `MIMAMORI_HOUR` | Hour to trigger mimamori (default: `8`) |
| `MIMAMORI_MINUTE` | Minute to trigger mimamori (default: `0`) |
| `ADMIN_TELEGRAM_BOT_TOKEN` | Admin bot token |
| `ADMIN_TELEGRAM_CHAT_ID` | Admin chat ID |

## Tests

```bash
cd bonsai_sensei
pytest tests/unit/
pytest tests/integration/ -m integration

# Acceptance tests (requires Docker):
bash tests/acceptance/run_acceptance.sh                          # all scenarios
bash tests/acceptance/run_acceptance.sh tests/acceptance/mimamori  # single module
bash tests/acceptance/run_acceptance.sh tests/acceptance/fertilization_plan "design_plan"  # with filter
```

## API

Swagger UI available at `http://localhost:8050/docs` when running locally.

Key endpoint groups: `/api/bonsai`, `/api/species`, `/api/fertilizers`, `/api/phytosanitary`, `/api/advice`, `/api/planned_works`, `/api/pests`.
