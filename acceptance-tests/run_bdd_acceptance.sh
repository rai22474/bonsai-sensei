#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

COMPOSE_FILE="acceptance-tests/docker-compose.acceptance.yml"
ACCEPTANCE_PORT="8060"
LOG_FILE="${ROOT_DIR}/acceptance-tests/docker-compose.logs.txt"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

if [ -z "${JUDGE_MODEL:-}" ] && [ -n "${GEMINI_MODEL:-}" ]; then
  export JUDGE_MODEL="gemini/${GEMINI_MODEL}"
fi

echo "Judge model for tests: ${JUDGE_MODEL:-unset} (GEMINI_MODEL=${GEMINI_MODEL:-unset})"
if [ -n "${JUDGE_API_KEY:-${GEMINI_API_KEY:-${GOOGLE_API_KEY:-}}}" ]; then
  echo "Judge API key detected."
else
  echo "Judge API key missing."
fi

run_step() {
  local label="$1"
  shift
  echo "Running: ${label}"
  if "$@"; then
    echo "Result: ${label} succeeded."
  else
    local status=$?
    echo "Result: ${label} failed (exit ${status})."
    return "$status"
  fi
}

clean_up() {
  set +e
  run_step "docker compose down (cleanup)" docker compose -f "$COMPOSE_FILE" down -v
  set -e
}

save_logs() {
  docker compose -f "$COMPOSE_FILE" logs --no-color > "$LOG_FILE"
}

trap clean_up EXIT

run_step "docker compose down" docker compose -f "$COMPOSE_FILE" down -v

run_step "docker compose build" docker compose -f "$COMPOSE_FILE" build

run_step "docker compose up" docker compose -f "$COMPOSE_FILE" up -d --no-build

ready=false
for i in {1..10}; do
  echo "Running: readiness check attempt ${i} (GET /api/species)"
  if curl -sf "http://localhost:${ACCEPTANCE_PORT}/api/species" >/dev/null; then
    echo "Result: readiness check attempt ${i} succeeded."
    ready=true
    break
  fi
  echo "Result: readiness check attempt ${i} failed."
  sleep 20
done

if [ "$ready" = false ]; then
  echo "Acceptance tests failed: API did not become ready on http://localhost:${ACCEPTANCE_PORT}."
  run_step "docker compose logs" save_logs
  echo "Docker logs saved to ${LOG_FILE}."
  exit 1
fi

if ! run_step "pytest acceptance-tests" env ACCEPTANCE_API_BASE="http://localhost:${ACCEPTANCE_PORT}" uv run pytest acceptance-tests -o python_files='*.py' -o python_functions='test_*' -o log_cli=true -o log_cli_level=INFO; then
  run_step "docker compose logs" save_logs
  echo "Docker logs saved to ${LOG_FILE}."
  echo "Acceptance tests failed: pytest reported errors."
  exit 1
fi

run_step "docker compose logs" save_logs
echo "Docker logs saved to ${LOG_FILE}."

run_step "docker compose down" docker compose -f "$COMPOSE_FILE" down -v
