# Bonsai Sensei

An intelligent assistant for Bonsai care.

## Features

- **Temperature-based Protection Advice**: Determine which bonsais need protection based on current weather conditions.
- **Bonsai Collection Management**: Create, list, update, and delete bonsais in your collection.
- **Species Registry**: Register species with care guides, update details, and delete entries.
- **Fertilizer Inventory**: Track fertilizers, update usage details, and remove products.
- **Phytosanitary Inventory**: Track phytosanitary products and their recommended uses.
- **Guided Confirmations**: Confirm create/update/delete operations via explicit accept/cancel flows.
- **Telegram Bot**: Chat with the assistant and receive confirmation prompts with buttons.
- **REST API**: FastAPI endpoints for advice, bonsai, species, fertilizers, phytosanitary, and weather.

## Agent Architecture

The system uses a CQRS pattern at the agent level: **read queries** are handled directly by sensei with lightweight tool calls, while **write commands** go through a planning and execution pipeline.

```
sensei                        [orchestrator model]
├── [query tools]             Direct read-only tools (no LLM hop)
│   ├── list_bonsai
│   ├── get_bonsai_by_name
│   ├── list_bonsai_events
│   ├── list_bonsai_species
│   ├── list_fertilizers
│   ├── list_phytosanitary
│   └── list_planned_works_for_bonsai
│
└── command_pipeline          SequentialAgent for write operations
    ├── mitori                Planner [orchestrator model]: analyses the request and produces a JSON action plan
    └── shokunin              Executor [leaf model]: runs the plan step by step using the agents below
        ├── botanist              Species registry (CRUD + care guides) [leaf model]
        ├── weather_advisor       Climate risk assessment [leaf model]
        ├── planning_agent        Cultivation plan — SequentialAgent
        │   ├── kikaku                Planner [orchestrator model]: schedules work and sets default dates
        │   └── seko                  Executor [leaf model]: runs plan steps using tools and advisors below
        │       ├── fertilizer_advisor    Recommends fertilizers based on history [leaf model]
        │       ├── phytosanitary_advisor Recommends phytosanitary products based on history [leaf model]
        │       └── [planning tools]      confirm_create/delete_planned_work, list_*, list_weekend_planned_works
        ├── gardener              Bonsai collection (CRUD + event recording) [leaf model]
        └── storekeeper           Fertilizer & phytosanitary catalogues (CRUD) [leaf model]
```

### Agent naming

Agents with domain-specific complexity are named after Japanese bonsai craft concepts:

| Name | Japanese | Meaning | Why |
|---|---|---|---|
| **sensei** | 先生 | teacher / master | The wise entry point that guides the user |
| **mitori** | 見取り | sketch / observe structure | Observes the request and drafts a structural plan before acting |
| **shokunin** | 職人 | craftsman | Executes the plan with precision, step by step |
| **kikaku** | 企画 | project planning | Plans the cultivation work schedule and decides dates |
| **seko** | 施工 | construction / implementation | Carries out the cultivation plan using tools and sub-agents |

Domain-facing agents (botanist, gardener, storekeeper, weather_advisor, fertilizer_advisor, phytosanitary_advisor) use descriptive English names that make their responsibility self-evident.

### Models

The system supports a dual-model setup via environment variables:

| Variable | Role | Default |
|---|---|---|
| `GEMINI_MODEL` | Leaf agents (botanist, weather_advisor, gardener, storekeeper, seko, advisors) | `gemini-2.0-flash-lite` |
| `GEMINI_ORCHESTRATOR_MODEL` | Orchestrators (sensei, mitori, kikaku) | falls back to `GEMINI_MODEL` |

### Roles

| Agent | Role |
|---|---|
| **sensei** | Entry point. Routes queries to direct tools, commands to `command_pipeline`. Formats responses for Telegram. |
| **mitori** | Planner. Reads the request and the available agent descriptions, then outputs a self-audited JSON action plan. |
| **shokunin** | Executor. Runs each step of mitori's plan, delegating to the appropriate leaf agent. Stops immediately on `confirmation_pending`. |
| **botanist** | Manages the species registry (CRUD). Resolves scientific names and generates care guides via external APIs at confirmation time. |
| **weather_advisor** | Fetches weather forecasts and advises on frost/heat protection for specific species. |
| **planning_agent** | Cultivation work calendar (fertilizations, transplants, treatments). Internal SequentialAgent: kikaku plans, seko executes. |
| **kikaku** | Planning planner. Analyses the scheduling request and decides dates — applies next-Saturday default when the user specifies none. |
| **seko** | Planning executor. Runs each step of kikaku's plan using tools and sub-advisors. |
| **fertilizer_advisor** | Recommends which fertilizer to use based on catalogue and bonsai event history. |
| **phytosanitary_advisor** | Recommends which phytosanitary product to use based on catalogue and event history. |
| **gardener** | Manages the bonsai collection (CRUD) and records completed events (fertilizations, transplants, treatments, planned work execution). |
| **storekeeper** | Manages the fertilizer and phytosanitary catalogues (CRUD). |

### Tools

| Agent | Tools |
|---|---|
| **sensei** | `list_bonsai`, `get_bonsai_by_name`, `list_bonsai_events`, `list_bonsai_species`, `list_fertilizers`, `list_phytosanitary`, `list_planned_works_for_bonsai`, `command_pipeline` |
| **mitori** | — |
| **shokunin** | `botanist`, `weather_advisor`, `planning_agent`, `gardener`, `storekeeper` |
| **botanist** | `confirm_create_bonsai_species`, `confirm_update_species`, `confirm_delete_species` |
| **weather_advisor** | `get_weather`, `get_user_location`, `list_bonsai_species` |
| **kikaku** | — |
| **seko** | `fertilizer_advisor`, `phytosanitary_advisor`, `list_planned_works_for_bonsai`, `list_bonsai_events_for_cultivation`, `confirm_create_planned_work`, `confirm_delete_planned_work`, `list_bonsai`, `list_weekend_planned_works` |
| **fertilizer_advisor** | `list_fertilizers_for_planning`, `list_bonsai_events_for_cultivation` |
| **phytosanitary_advisor** | `list_phytosanitary_for_planning`, `list_bonsai_events_for_cultivation` |
| **gardener** | `list_bonsai`, `get_bonsai_by_name`, `confirm_create_bonsai`, `confirm_update_bonsai`, `confirm_delete_bonsai`, `confirm_apply_fertilizer`, `confirm_apply_phytosanitary`, `confirm_record_transplant`, `list_bonsai_events`, `list_planned_works_for_bonsai`, `confirm_execute_planned_work` |
| **storekeeper** | `list_fertilizers`, `confirm_create_fertilizer`, `confirm_update_fertilizer`, `confirm_delete_fertilizer`, `list_phytosanitary`, `confirm_create_phytosanitary`, `confirm_update_phytosanitary`, `confirm_delete_phytosanitary` |

### Confirmation flow

Write operations that mutate data require explicit user confirmation. The leaf agent calls a `confirm_*` tool which queues the operation and returns `confirmation_pending`. Shokunin stops execution and sensei surfaces the pending confirmation to the user as a Telegram button. The operation executes only after the user taps "Accept".

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker (optional, for containerization)
- Ollama installed for local model mode

## Installation

1.  Clone the repository.
2.  Install dependencies:

    ```bash
    uv sync
    ```

## Running Locally

Run the server with:

```bash
uv run uvicorn bonsai_sensei.main:app --reload
```

Open http://127.0.0.1:8000/docs to see the Swagger UI.

## Acceptance tests (BDD)

Run the BDD acceptance test suite against the local model stack:

```bash
./acceptance-tests/run_bdd_acceptance.sh
```

The acceptance tests use HTTP stubs for external services like weather.

## Observability (Monocle)

Monocle observability is disabled by default. To enable it, set the environment variables below:

- `MONOCLE_ENABLED=true`
- `MONOCLE_WORKFLOW_NAME=bonsai-sensei`
- `MONOCLE_EXPORTERS=console` (optional)

## Docker

### Local model (Ollama)

Start Ollama and pull the model if needed:

```bash
./scripts/start_ollama.sh

By default this pulls `qwen2.5:32b-instruct`. Override by passing another model name.
```

Start the stack using the local model:

```bash
./scripts/start_applications.sh local
```

### Cloud model

Start the stack using the cloud model:

```bash
./scripts/start_applications.sh cloud
```

Build the image:

```bash
docker build -t bonsai-sensei .
```

Run the container:

```bash
docker run -p 8000:8000 bonsai-sensei
```

Open http://127.0.0.1:8000/docs.

## GCP deployment (Cloud Run + Cloud SQL + Pulumi + Cloud Build)

This project includes infrastructure as code in `infra/` and a `cloudbuild.yaml` pipeline.

### Infrastructure deployed

Pulumi provisions the following GCP resources:

- Artifact Registry (Docker) repository for container images.
- Cloud SQL Postgres 15 instance, database, and user.
- Secret Manager secret storing the `DATABASE_URL`.
- Cloud Run service wired to Cloud SQL via Unix socket and Secret Manager.
- Service account with Cloud SQL client and Secret Manager access.
- Cloud Build trigger for GitHub pushes using `cloudbuild.yaml`.

### Cost-aware defaults

- Cloud Run scales to zero and uses a single max instance by default.
- Cloud SQL uses the smallest tier and zonal availability.
- Cloud SQL does not have a free tier, so expect minimal but non-zero cost.

### Required setup

1. Enable Cloud Run, Cloud Build, Artifact Registry, Cloud SQL, and Secret Manager APIs.
2. Create a Secret Manager secret named `pulumi-access-token` with a Pulumi access token value.
3. Configure a Pulumi stack in `infra/` (dependencies are defined in `infra/pyproject.toml`) and set the required config:
    - `dbPassword` (secret)
    - `image` (container image reference)
    - Optional: `project`, `region`, `serviceName`, `dbName`, `dbUser`, `maxInstances`

### Local deployment script

`infra/deploy_local.sh` configures Pulumi and runs `pulumi up` from your machine.

```bash
PROJECT_ID="your-project-id" DB_PASSWORD="your-db-password" ./infra/deploy_local.sh
```

Optional overrides:

```bash
REGION="europe-west1" SERVICE_NAME="bonsai-sensei-api" REPOSITORY="bonsai-sensei" IMAGE_TAG="latest" \
PULUMI_STACK="dev" REPO_OWNER="rai22474" REPO_NAME="bonsai-sensei" REPO_BRANCH="main" \
BUILD_CONFIG_PATH="cloudbuild.yaml" ./infra/deploy_local.sh
```

### Cloud Build deployment flow

`cloudbuild.yaml` builds and pushes the image, then runs `pulumi up` to deploy Cloud Run and Cloud SQL.
The service is deployed without public access; grant `roles/run.invoker` to specific identities as needed.

### Database connection

The service reads `DATABASE_URL` from Secret Manager and connects via the Cloud SQL Unix socket.
