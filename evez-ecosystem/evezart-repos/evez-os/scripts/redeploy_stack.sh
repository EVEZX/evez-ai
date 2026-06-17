#!/usr/bin/env bash
set -euo pipefail

STABLE_BRANCH="${STABLE_BRANCH:-stable}"
REPO_DIR="${REPO_DIR:-$PWD}"
COMPOSE_FILE="${COMPOSE_FILE:-core/docker-compose.yml}"

cd "$REPO_DIR"

echo "[redeploy] syncing branch ${STABLE_BRANCH}"
git fetch origin "$STABLE_BRANCH"
git checkout "$STABLE_BRANCH"
git reset --hard "origin/$STABLE_BRANCH"

echo "[redeploy] rebuilding and starting stack"
docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
docker compose -f "$COMPOSE_FILE" pull || true
docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans

echo "[redeploy] stack status"
docker compose -f "$COMPOSE_FILE" ps
