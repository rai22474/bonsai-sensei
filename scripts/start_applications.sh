#!/bin/bash
set -e

echo "Starting Bonsai Sensei Stack with Docker Compose..."

# Ensure postgres_data exists and has correct permissions
if [ ! -d "postgres_data" ]; then
    echo "Creating postgres_data directory..."
    mkdir -p postgres_data
fi
# Grant write permissions to be safe (fixes some Docker mount permission issues)
chmod 777 postgres_data

docker compose down # Clean up previous containers
docker compose up --build -d

echo "Stack started in background."
echo "App running at http://localhost:8050"
echo "To see logs: docker compose logs -f"
