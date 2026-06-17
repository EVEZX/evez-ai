#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT/docker-compose.linux-matrix.yml"
ENV_FILE="$ROOT/.env"
usage() {
  cat <<USAGE
Usage: $0 {up|down|restart|status|logs|doctor|config|pull-build}

Runs OpenClaw on multiple nonlocal Linux runtimes:
  - Ubuntu 24.04 host container -> localhost:18789
  - Ubuntu 22.04 host container -> localhost:18790
  - Debian 12 host container    -> localhost:18791

Secrets are read from $ENV_FILE. Generate a gateway token with:
  openssl rand -hex 32
USAGE
}
compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  else
    echo "ERROR: Docker Compose not found." >&2
    exit 127
  fi
}
require_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    cp "$ROOT/.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE" 2>/dev/null || true
    echo "Created $ENV_FILE. Fill OPENCLAW_GATEWAY_TOKEN and provider/channel keys, then rerun." >&2
    exit 64
  fi
  if ! grep -q '^OPENCLAW_GATEWAY_TOKEN=.' "$ENV_FILE"; then
    echo "ERROR: set OPENCLAW_GATEWAY_TOKEN in $ENV_FILE before starting remote Linux runtimes." >&2
    exit 64
  fi
}
cmd="${1:-}"; shift || true
case "$cmd" in
  up) require_env; compose up -d --build "$@" ;;
  pull-build) require_env; compose build --pull "$@" ;;
  down) compose down "$@" ;;
  restart) require_env; compose up -d --build --force-recreate "$@" ;;
  status) compose ps "$@" ;;
  logs) compose logs -f --tail=150 "$@" ;;
  config) require_env; compose config "$@" ;;
  doctor)
    require_env
    compose ps
    for svc in openclaw-ubuntu-2404 openclaw-ubuntu-2204 openclaw-debian-12; do
      echo "--- $svc ---"
      compose exec -T "$svc" sh -lc 'openclaw gateway health --url ws://127.0.0.1:18789 --token "$OPENCLAW_GATEWAY_TOKEN" --timeout 5000 && lobster "openclaw.invoke --tool agents_list --action json --args-json {} | json" | head -c 400; echo'
    done
    ;;
  *) usage; exit 64 ;;
esac
