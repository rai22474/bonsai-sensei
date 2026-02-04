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
