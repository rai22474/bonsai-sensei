#!/bin/bash
set -e

MODE=${1:-cloud}
if [ "$MODE" != "local" ] && [ "$MODE" != "cloud" ]; then
    echo "Usage: $0 [local|cloud]"
    exit 1
fi

echo "Starting Bonsai Sensei Stack with Docker Compose... (mode: $MODE)"

# Ensure postgres_data exists and has correct permissions
if [ ! -d "postgres_data" ]; then
    echo "Creating postgres_data directory..."
    mkdir -p postgres_data
fi
# Grant write permissions to be safe (fixes some Docker mount permission issues)
chmod 777 postgres_data

docker compose down

if [ "$MODE" = "local" ]; then
    export MODEL_PROVIDER=local
    export OLLAMA_API_BASE=http://host.docker.internal:11434
    export OLLAMA_MODEL=mistral-small3.1
    if ! curl -s http://localhost:11434/api/status >/dev/null 2>&1; then
        scripts/start_ollama.sh "$OLLAMA_MODEL"
    fi
    docker compose up --build -d db
    docker compose up --build -d --force-recreate --no-deps app
else
    export MODEL_PROVIDER=cloud
    docker compose up --build -d db
    docker compose up --build -d --force-recreate app
fi

echo "Stack started in background."
echo "App running at http://localhost:8050"
echo "To see logs: docker compose logs -f"
