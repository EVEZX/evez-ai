#!/usr/bin/env sh
set -eu
: "${OPENCLAW_STATE_DIR:=/opt/openclaw/state}"
: "${OPENCLAW_CONFIG_PATH:=$OPENCLAW_STATE_DIR/openclaw.json}"
: "${OPENCLAW_WORKSPACE_DIR:=$OPENCLAW_STATE_DIR/workspace}"
: "${OPENCLAW_PORT:=18789}"
: "${OPENCLAW_BIND:=lan}"
: "${OPENCLAW_TELEGRAM_ALLOW_FROM:=}"
: "${LOBSTER_STATE_DIR:=$OPENCLAW_STATE_DIR/lobster}"
if [ -z "${OPENCLAW_URL:-}" ]; then export OPENCLAW_URL="http://127.0.0.1:${OPENCLAW_PORT}"; fi
if [ -z "${OPENCLAW_TOKEN:-}" ] && [ -n "${OPENCLAW_GATEWAY_TOKEN:-}" ]; then export OPENCLAW_TOKEN="$OPENCLAW_GATEWAY_TOKEN"; fi
if [ -z "${CLAWD_URL:-}" ]; then export CLAWD_URL="$OPENCLAW_URL"; fi
if [ -z "${EVEZ_CK_TOKEN:-}" ] && [ -n "${CK_TOKEN:-}" ]; then export EVEZ_CK_TOKEN="$CK_TOKEN"; fi
if [ -z "${CLAWD_TOKEN:-}" ] && [ -n "${CK_TOKEN:-}" ]; then export CLAWD_TOKEN="$CK_TOKEN"; fi
if [ -z "${GH_TOKEN:-}" ] && [ -n "${GITHUB_TOKEN:-}" ]; then export GH_TOKEN="$GITHUB_TOKEN"; fi
mkdir -p "$OPENCLAW_STATE_DIR" "$OPENCLAW_WORKSPACE_DIR" "$OPENCLAW_STATE_DIR/credentials" "$OPENCLAW_STATE_DIR/logs" "$OPENCLAW_STATE_DIR/run" "$LOBSTER_STATE_DIR"
chmod 700 "$OPENCLAW_STATE_DIR" 2>/dev/null || true
if [ ! -f "$OPENCLAW_CONFIG_PATH" ] || [ "${EVEZ_OPENCLAW_OVERWRITE_CONFIG:-0}" = "1" ]; then
  cp /opt/evez-openclaw-deploy/openclaw.json "$OPENCLAW_CONFIG_PATH"
fi
python3 - "$OPENCLAW_CONFIG_PATH" <<'PYCFG'
import json, os, pathlib, sys
p=pathlib.Path(sys.argv[1])
c=json.load(p.open())
port=int(os.environ.get('OPENCLAW_PORT','18789'))
bind=os.environ.get('OPENCLAW_BIND','lan')
workspace=os.environ.get('OPENCLAW_WORKSPACE_DIR','/opt/openclaw/state/workspace')
c.setdefault('gateway',{})['mode']='local'
c['gateway']['port']=port
c['gateway']['bind']=bind
c['gateway'].setdefault('auth',{})['mode']='token'
c['gateway'].setdefault('controlUi',{})['basePath']='/'
c.setdefault('agents',{}).setdefault('defaults',{})['workspace']=workspace
model=c['agents']['defaults'].setdefault('model',{})
if os.environ.get('GROQ_API_KEY'):
    model['primary']='groq/llama-3.3-70b-versatile'
    model['fallbacks']=['openrouter/meta-llama/llama-3.3-70b-instruct:free','openrouter/openai/gpt-oss-20b:free','openrouter/qwen/qwen3-coder:free','groq/llama-3.1-8b-instant']
c.setdefault('channels',{}).setdefault('telegram',{})['enabled']=bool(os.environ.get('TELEGRAM_BOT_TOKEN') or os.environ.get('OPENCLAW_TELEGRAM_ALLOW_FROM'))
c['channels'].setdefault('slack',{})['enabled']=bool(os.environ.get('SLACK_BOT_TOKEN') and os.environ.get('SLACK_APP_TOKEN'))
entries=c.setdefault('plugins',{}).setdefault('entries',{})
for name in ['memory-core','llm-task','open-prose','copilot-proxy','lobster']:
    entries.setdefault(name,{})['enabled']=True
entries.setdefault('telegram',{})['enabled']=c['channels']['telegram']['enabled']
entries.setdefault('slack',{})['enabled']=c['channels']['slack']['enabled']
c.setdefault('tools',{})['alsoAllow']=sorted(set(c.get('tools',{}).get('alsoAllow',[])+['agents_list','llm-task']))
json.dump(c, p.open('w'), indent=2)
p.chmod(0o600)
PYCFG
if [ -d /opt/evez-openclaw-deploy/workspace ]; then
  cp -Rn /opt/evez-openclaw-deploy/workspace/. "$OPENCLAW_WORKSPACE_DIR/" 2>/dev/null || true
fi
if [ -f /opt/evez-openclaw-deploy/runtime/agentvault-connector.json ]; then
  cp /opt/evez-openclaw-deploy/runtime/agentvault-connector.json "$OPENCLAW_STATE_DIR/agentvault-connector.json"
  chmod 600 "$OPENCLAW_STATE_DIR/agentvault-connector.json" 2>/dev/null || true
fi
if [ -n "$OPENCLAW_TELEGRAM_ALLOW_FROM" ]; then
  python3 - "$OPENCLAW_STATE_DIR/credentials/telegram-allowFrom.json" "$OPENCLAW_TELEGRAM_ALLOW_FROM" <<'PY'
import json,sys
ids=[x.strip() for x in sys.argv[2].replace(';',',').split(',') if x.strip()]
json.dump({"version":1,"allowFrom":ids}, open(sys.argv[1],"w"), indent=2)
PY
  chmod 600 "$OPENCLAW_STATE_DIR/credentials/telegram-allowFrom.json" 2>/dev/null || true
fi

AUTH_AGENT_DIR="$OPENCLAW_STATE_DIR/agents/main/agent"
AUTH_STORE="$AUTH_AGENT_DIR/auth-profiles.json"
mkdir -p "$AUTH_AGENT_DIR"
python3 - "$AUTH_STORE" <<'PYAUTH'
import json, os, pathlib, sys
out=pathlib.Path(sys.argv[1])
providers={
  "groq":"GROQ_API_KEY","openrouter":"OPENROUTER_API_KEY","openai":"OPENAI_API_KEY","anthropic":"ANTHROPIC_API_KEY",
  "google":"GEMINI_API_KEY","cerebras":"CEREBRAS_API_KEY","deepseek":"DEEPSEEK_API_KEY","mistral":"MISTRAL_API_KEY",
  "xai":"XAI_API_KEY","together":"TOGETHER_API_KEY","fireworks":"FIREWORKS_API_KEY","nvidia":"NVIDIA_API_KEY",
  "deepinfra":"DEEPINFRA_API_KEY","novita":"NOVITA_API_KEY"
}
if out.exists():
    try: payload=json.load(out.open())
    except Exception: payload={"version":1,"profiles":{}}
else: payload={"version":1,"profiles":{}}
payload.setdefault('version',1)
profiles=payload.setdefault("profiles",{}); order=payload.setdefault("order",{})
for provider, env_name in providers.items():
    key=os.environ.get(env_name, "").strip()
    if key:
        pid=f"{provider}:env"; profiles[pid]={"type":"api_key","provider":provider,"key":key}; order.setdefault(provider,[])
        if pid not in order[provider]: order[provider].insert(0,pid)
if not order: payload.pop("order", None)
json.dump(payload, out.open("w"), indent=2); out.chmod(0o600)
PYAUTH

if [ -z "${OPENCLAW_GATEWAY_TOKEN:-}" ]; then
  echo "ERROR: OPENCLAW_GATEWAY_TOKEN must be set as a secret/env var so the Control UI can connect." >&2
  exit 64
fi
cat > "$OPENCLAW_STATE_DIR/openclaw.env" <<ENV
OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN
OPENCLAW_URL=$OPENCLAW_URL
OPENCLAW_TOKEN=$OPENCLAW_TOKEN
CLAWD_URL=$CLAWD_URL
CLAWD_TOKEN=${CLAWD_TOKEN:-}
CK_TOKEN=${CK_TOKEN:-}
EVEZ_CK_TOKEN=${EVEZ_CK_TOKEN:-}
OPENCLAW_STATE_DIR=$OPENCLAW_STATE_DIR
OPENCLAW_CONFIG_PATH=$OPENCLAW_CONFIG_PATH
OPENCLAW_WORKSPACE_DIR=$OPENCLAW_WORKSPACE_DIR
LOBSTER_STATE_DIR=$LOBSTER_STATE_DIR
ENV
chmod 600 "$OPENCLAW_STATE_DIR/openclaw.env" 2>/dev/null || true
exec "$@" --token "$OPENCLAW_GATEWAY_TOKEN"
