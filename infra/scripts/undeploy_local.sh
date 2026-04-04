#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

PROJECT_ID="${PROJECT_ID:-}"
PULUMI_STACK="${PULUMI_STACK:-dev}"
PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE:-}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is required"
  exit 1
fi

if [[ -z "$PULUMI_CONFIG_PASSPHRASE" ]]; then
  echo "PULUMI_CONFIG_PASSPHRASE is required"
  exit 1
fi

export PULUMI_CONFIG_PASSPHRASE

cd "${ROOT_DIR}/infra"
pulumi stack select "${PULUMI_STACK}"
pulumi destroy --yes
