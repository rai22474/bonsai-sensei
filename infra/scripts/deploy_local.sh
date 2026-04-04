#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  source "${ROOT_DIR}/.env"
  set +a
fi

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-europe-southwest1}"
DB_REGION="${DB_REGION:-europe-southwest1}"
SCHEDULER_REGION="${SCHEDULER_REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-bonsai-sensei-api}"
REPOSITORY="${REPOSITORY:-bonsai-sensei}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DB_PASSWORD="${DB_PASSWORD:-}"
PULUMI_STACK="${PULUMI_STACK:-dev}"
PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE:-}"
GITHUB_OWNER="${GITHUB_OWNER:-}"
GITHUB_REPO="${GITHUB_REPO:-bonsai-sensei}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is required"
  exit 1
fi

if [[ -z "$DB_PASSWORD" ]]; then
  echo "DB_PASSWORD is required"
  exit 1
fi

if [[ -z "$PULUMI_CONFIG_PASSPHRASE" ]]; then
  echo "PULUMI_CONFIG_PASSPHRASE is required (used to encrypt secrets in local state)"
  exit 1
fi

if [[ -z "$GITHUB_OWNER" ]]; then
  echo "GITHUB_OWNER is required (your GitHub username or organization)"
  exit 1
fi

export PULUMI_CONFIG_PASSPHRASE

PLACEHOLDER_IMAGE="gcr.io/cloudrun/hello"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/bonsai-sensei:${IMAGE_TAG}"

if gcloud artifacts docker images describe "${IMAGE_URI}" --quiet 2>/dev/null; then
  DEPLOY_IMAGE="${IMAGE_URI}"
else
  echo "Image ${IMAGE_URI} not found in Artifact Registry, using placeholder ${PLACEHOLDER_IMAGE}"
  DEPLOY_IMAGE="${PLACEHOLDER_IMAGE}"
fi

cd "${ROOT_DIR}/infra"
uv venv .venv --seed --quiet
uv pip install --quiet --python .venv/bin/python -e .
pulumi stack init "${PULUMI_STACK}" 2>/dev/null || pulumi stack select "${PULUMI_STACK}"
pulumi config set gcp:project "${PROJECT_ID}"
pulumi config set gcp:region "${REGION}"
pulumi config set project "${PROJECT_ID}"
pulumi config set region "${REGION}"
pulumi config set dbRegion "${DB_REGION}"
pulumi config set schedulerRegion "${SCHEDULER_REGION}"
pulumi config set serviceName "${SERVICE_NAME}"
pulumi config set image "${DEPLOY_IMAGE}"
pulumi config set --secret dbPassword "${DB_PASSWORD}"
pulumi config set githubOwner "${GITHUB_OWNER}"
pulumi config set githubRepo "${GITHUB_REPO}"

pulumi import gcp:iam/workloadIdentityPool:WorkloadIdentityPool github-pool \
  "projects/${PROJECT_ID}/locations/global/workloadIdentityPools/github-pool" --yes 2>/dev/null || true
pulumi import gcp:iam/workloadIdentityPoolProvider:WorkloadIdentityPoolProvider github-provider \
  "projects/${PROJECT_ID}/locations/global/workloadIdentityPools/github-pool/providers/github-provider" --yes 2>/dev/null || true
pulumi import gcp:serviceaccount/account:Account github-actions-deployer \
  "projects/${PROJECT_ID}/serviceAccounts/github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com" --yes 2>/dev/null || true

pulumi up --yes
