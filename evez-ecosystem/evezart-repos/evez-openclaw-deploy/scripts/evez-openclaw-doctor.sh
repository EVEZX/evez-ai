#!/usr/bin/env bash
set -euo pipefail
: "${OPENCLAW_STATE_DIR:=$HOME/.openclaw}"
: "${OPENCLAW_CONFIG_PATH:=$OPENCLAW_STATE_DIR/openclaw.json}"
: "${OPENCLAW_PORT:=18789}"
: "${OPENCLAW_BIN:=openclaw}"
ENV_FILE="$OPENCLAW_STATE_DIR/openclaw.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi
printf 'OpenClaw binary: '
if command -v "$OPENCLAW_BIN" >/dev/null 2>&1; then command -v "$OPENCLAW_BIN"; else echo "missing ($OPENCLAW_BIN)"; fi
printf 'State dir: %s\nConfig: %s\n' "$OPENCLAW_STATE_DIR" "$OPENCLAW_CONFIG_PATH"
if [[ -f "$OPENCLAW_CONFIG_PATH" ]]; then echo 'Config exists'; else echo 'Config missing'; fi
if [[ -f "$OPENCLAW_STATE_DIR/agentvault-connector.json" ]]; then echo 'AgentVault connector profile exists'; else echo 'AgentVault connector profile missing'; fi
if command -v "$OPENCLAW_BIN" >/dev/null 2>&1 && [[ -n "${OPENCLAW_GATEWAY_TOKEN:-}" ]]; then
  if env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" OPENCLAW_GATEWAY_TOKEN="$OPENCLAW_GATEWAY_TOKEN" \
    "$OPENCLAW_BIN" gateway health --url "ws://127.0.0.1:$OPENCLAW_PORT" --token "$OPENCLAW_GATEWAY_TOKEN" --timeout 5000; then
    true
  else
    echo 'Gateway WS health failed'
  fi
  "$OPENCLAW_BIN" gateway status --json || true
else
  echo 'Gateway health skipped: missing binary or token'
fi

AUTH_STORE="$OPENCLAW_STATE_DIR/agents/main/agent/auth-profiles.json"
echo 'Provider auth profiles:'
if [[ -f "$AUTH_STORE" ]]; then
  python3 - "$AUTH_STORE" <<'PYAUTHCHK'
import json,sys
p=sys.argv[1]
try:
    j=json.load(open(p))
except Exception as e:
    print(f"  invalid auth store: {e}")
    sys.exit(0)
profiles=j.get('profiles') or {}
by_provider={}
for pid, cred in profiles.items():
    provider=(cred or {}).get('provider')
    if provider and (cred or {}).get('type') in {'api_key','token','oauth'}:
        by_provider.setdefault(provider,0); by_provider[provider]+=1
if by_provider:
    for provider,count in sorted(by_provider.items()):
        print(f"  {provider}: {count} profile(s)")
else:
    print('  missing provider keys: set GROQ_API_KEY or OPENROUTER_API_KEY (or another provider key) and rerun recover')
PYAUTHCHK
else
  echo '  missing auth-profiles.json: set GROQ_API_KEY or OPENROUTER_API_KEY and rerun recover'
fi
if [[ -f "$OPENCLAW_STATE_DIR/workspace/EVEZ_IDENTITY.md" ]]; then echo 'EVEZ identity seed exists'; else echo 'EVEZ identity seed missing'; fi
if [[ -f "$OPENCLAW_STATE_DIR/workspace/ecosystem/github-public-repos.json" ]]; then echo 'EVEZ public repo inventory exists'; else echo 'EVEZ public repo inventory missing'; fi
if [[ -f "$OPENCLAW_STATE_DIR/workspace/private/github-visible-repos-private.json" ]]; then echo 'EVEZ private local repo inventory exists'; fi
if command -v "$OPENCLAW_BIN" >/dev/null 2>&1; then
  echo 'Plugins:'
  env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" "$OPENCLAW_BIN" plugins list || true
  echo 'Skills:'
  env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" "$OPENCLAW_BIN" skills check || true
  env OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR" OPENCLAW_CONFIG_PATH="$OPENCLAW_CONFIG_PATH" "$OPENCLAW_BIN" models status --plain --agent main || true
fi
