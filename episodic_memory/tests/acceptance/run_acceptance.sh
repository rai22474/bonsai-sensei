#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$ROOT_DIR"

COMPOSE_FILE="episodic_memory/tests/acceptance/docker-compose.acceptance.yml"
ACCEPTANCE_PORT="8070"
LOG_FILE="${ROOT_DIR}/episodic_memory/tests/acceptance/docker-compose.logs.txt"
TEST_TARGET="${1:-all}"
SCENARIO_FILTER="${2:-}"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
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
  echo "Running: readiness check attempt ${i} (GET /health)"
  if curl -sf "http://localhost:${ACCEPTANCE_PORT}/health" >/dev/null; then
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

if [ "$TEST_TARGET" = "all" ]; then
  PYTEST_TARGET="episodic_memory/tests/acceptance"
else
  PYTEST_TARGET="$TEST_TARGET"
fi

PYTEST_LOG="${ROOT_DIR}/episodic_memory/tests/acceptance/pytest.log"
PYTEST_ARGS=("$PYTEST_TARGET" -o python_files='*.py' -o python_functions='test_*' -o log_cli=true -o log_cli_level=INFO --tb=short)
if [ -n "$SCENARIO_FILTER" ]; then
  PYTEST_ARGS+=("-k" "$SCENARIO_FILTER")
fi

if ! run_step "pytest ${PYTEST_TARGET}" env ACCEPTANCE_API_BASE="http://localhost:${ACCEPTANCE_PORT}" uv run --project "${ROOT_DIR}/episodic_memory" pytest "${PYTEST_ARGS[@]}" 2>&1 | tee "$PYTEST_LOG"; then
  run_step "docker compose logs" save_logs
  echo "Docker logs saved to ${LOG_FILE}."
  echo "Pytest output saved to ${PYTEST_LOG}."
  echo "Acceptance tests failed: pytest reported errors."
  exit 1
fi

run_step "docker compose logs" save_logs
echo "Docker logs saved to ${LOG_FILE}."
echo "Pytest output saved to ${PYTEST_LOG}."

run_step "docker compose down" docker compose -f "$COMPOSE_FILE" down -v
