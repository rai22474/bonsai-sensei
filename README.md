# Bonsai Sensei

An intelligent assistant for Bonsai care.

## Features

- **Temperature-based Protection Advice**: Determine which bonsais need protection based on current weather conditions.

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
