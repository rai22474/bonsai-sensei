#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-bonsai-sensei-api}"
REPOSITORY="${REPOSITORY:-bonsai-sensei}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DB_PASSWORD="${DB_PASSWORD:-}"
PULUMI_STACK="${PULUMI_STACK:-dev}"
REPO_OWNER="${REPO_OWNER:-rai22474}"
REPO_NAME="${REPO_NAME:-bonsai-sensei}"
REPO_BRANCH="${REPO_BRANCH:-main}"
BUILD_CONFIG_PATH="${BUILD_CONFIG_PATH:-cloudbuild.yaml}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is required"
  exit 1
fi

if [[ -z "$DB_PASSWORD" ]]; then
  echo "DB_PASSWORD is required"
  exit 1
fi

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/bonsai-sensei:${IMAGE_TAG}"

cd infra
pulumi stack init "${PULUMI_STACK}" >/dev/null 2>&1 || pulumi stack select "${PULUMI_STACK}"
pulumi config set project "${PROJECT_ID}"
pulumi config set region "${REGION}"
pulumi config set serviceName "${SERVICE_NAME}"
pulumi config set image "${IMAGE_URI}"
pulumi config set repoOwner "${REPO_OWNER}"
pulumi config set repoName "${REPO_NAME}"
pulumi config set repoBranch "${REPO_BRANCH}"
pulumi config set buildConfigPath "${BUILD_CONFIG_PATH}"
pulumi config set pulumiStack "${PULUMI_STACK}"
pulumi config set --secret dbPassword "${DB_PASSWORD}"
pulumi up --yes
