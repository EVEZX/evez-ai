#!/bin/bash
# ============================================================
# EVEZ OpenClaw Mesh — Full Deploy Script
# Deploys all 3 nodes to Fly.io and sets secrets
#
# Usage:
#   ./deploy.sh                    # Deploy all nodes
#   ./deploy.sh secrets            # Just set secrets (no deploy)
#   ./deploy.sh restart            # Restart all machines
#   ./deploy.sh alpha              # Deploy only alpha node
#
# Prerequisites:
#   fly auth login  (or: export FLY_API_TOKEN=...)
# ============================================================

set -euo pipefail

# ── Config ────────────────────────────────────────────────────

ALPHA_APP="openclaws-qol4-a"
BETA_APP="openclaw-pfncdg"
BRAIN_APP="evez666"

APPS=("$ALPHA_APP" "$BETA_APP" "$BRAIN_APP")

# Source secrets from .env if present
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded secrets from .env"
fi

# ── Validate flyctl ────────────────────────────────────────────

if ! command -v fly &>/dev/null && ! command -v flyctl &>/dev/null; then
    echo "❌ flyctl not found. Install: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

FLY=$(command -v fly 2>/dev/null || command -v flyctl 2>/dev/null)
echo "✅ Using: $FLY"

# ── Helper: set secrets for an app ───────────────────────────

set_secrets() {
    local app="$1"
    echo "🔑 Setting secrets for $app..."
    
    local secrets=()
    
    # LLM Providers — always set if available
    [[ -n "${OPENROUTER_API_KEY:-}" ]]      && secrets+=("OPENROUTER_API_KEY=$OPENROUTER_API_KEY")
    [[ -n "${GROQ_API_KEY:-}" ]]            && secrets+=("GROQ_API_KEY=$GROQ_API_KEY")
    [[ -n "${ANTHROPIC_API_KEY:-}" ]]       && secrets+=("ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY")
    [[ -n "${GEMINI_API_KEY:-}" ]]          && secrets+=("GEMINI_API_KEY=$GEMINI_API_KEY")
    [[ -n "${PERPLEXITY_API_KEY:-}" ]]      && secrets+=("PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY")
    [[ -n "${MINIMAX_API_KEY:-}" ]]         && secrets+=("MINIMAX_API_KEY=$MINIMAX_API_KEY")
    [[ -n "${VENICE_API_KEY:-}" ]]          && secrets+=("VENICE_API_KEY=$VENICE_API_KEY")
    [[ -n "${KIMI_API_KEY:-}" ]]            && secrets+=("KIMI_API_KEY=$KIMI_API_KEY")
    [[ -n "${ZAI_API_KEY:-}" ]]             && secrets+=("ZAI_API_KEY=$ZAI_API_KEY")
    [[ -n "${Z_AI_API_KEY:-}" ]]            && secrets+=("Z_AI_API_KEY=$Z_AI_API_KEY")
    [[ -n "${DEEPGRAM_API_KEY:-}" ]]        && secrets+=("DEEPGRAM_API_KEY=$DEEPGRAM_API_KEY")
    [[ -n "${ELEVENLABS_API_KEY:-}" ]]      && secrets+=("ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY")
    [[ -n "${FIRECRAWL_API_KEY:-}" ]]       && secrets+=("FIRECRAWL_API_KEY=$FIRECRAWL_API_KEY")
    [[ -n "${BRAVE_API_KEY:-}" ]]           && secrets+=("BRAVE_API_KEY=$BRAVE_API_KEY")
    [[ -n "${COPILOT_GITHUB_TOKEN:-}" ]]    && secrets+=("COPILOT_GITHUB_TOKEN=$COPILOT_GITHUB_TOKEN")
    [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]       && secrets+=("AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID")
    [[ -n "${AWS_SECRET_ACCESS_KEY:-}" ]]   && secrets+=("AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY")
    [[ -n "${CLAUDE_AI_SESSION_KEY:-}" ]]   && secrets+=("CLAUDE_AI_SESSION_KEY=$CLAUDE_AI_SESSION_KEY")
    [[ -n "${CLAUDE_WEB_SESSION_KEY:-}" ]]  && secrets+=("CLAUDE_WEB_SESSION_KEY=$CLAUDE_WEB_SESSION_KEY")
    [[ -n "${CLAUDE_WEB_COOKIE:-}" ]]       && secrets+=("CLAUDE_WEB_COOKIE=$CLAUDE_WEB_COOKIE")
    
    # Messaging channels
    [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]             && secrets+=("TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN")
    [[ -n "${DISCORD_BOT_TOKEN:-}" ]]              && secrets+=("DISCORD_BOT_TOKEN=$DISCORD_BOT_TOKEN")
    [[ -n "${SLACK_BOT_TOKEN:-}" ]]                && secrets+=("SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN")
    [[ -n "${SLACK_APP_TOKEN:-}" ]]                && secrets+=("SLACK_APP_TOKEN=$SLACK_APP_TOKEN")
    [[ -n "${LINE_CHANNEL_ACCESS_TOKEN:-}" ]]      && secrets+=("LINE_CHANNEL_ACCESS_TOKEN=$LINE_CHANNEL_ACCESS_TOKEN")
    [[ -n "${LINE_CHANNEL_SECRET:-}" ]]            && secrets+=("LINE_CHANNEL_SECRET=$LINE_CHANNEL_SECRET")
    [[ -n "${SYNTHETIC_API_KEY:-}" ]]              && secrets+=("SYNTHETIC_API_KEY=$SYNTHETIC_API_KEY")
    [[ -n "${CHUTES_CLIENT_ID:-}" ]]               && secrets+=("CHUTES_CLIENT_ID=$CHUTES_CLIENT_ID")
    [[ -n "${CHUTES_CLIENT_SECRET:-}" ]]           && secrets+=("CHUTES_CLIENT_SECRET=$CHUTES_CLIENT_SECRET")
    [[ -n "${GITHUB_TOKEN:-}" ]]                   && secrets+=("GITHUB_TOKEN=$GITHUB_TOKEN")

    if [ ${#secrets[@]} -gt 0 ]; then
        $FLY secrets set --app "$app" "${secrets[@]}" 2>&1 | tail -3
        echo "  ✅ Set ${#secrets[@]} secrets for $app"
    else
        echo "  ⚠️  No secrets found for $app (check your .env)"
    fi
}

# ── Helper: restart a machine ────────────────────────────────

restart_app() {
    local app="$1"
    echo "🔄 Restarting machines for $app..."
    $FLY machines list --app "$app" 2>/dev/null | grep -oP '[0-9a-f]{14,}' | while read mid; do
        $FLY machines start "$mid" --app "$app" 2>/dev/null && echo "  ✅ Started machine $mid" || \
        $FLY machines restart "$mid" --app "$app" 2>/dev/null && echo "  ✅ Restarted machine $mid" || \
        echo "  ⚠️  Could not start $mid"
    done
}

# ── Main Deploy Logic ─────────────────────────────────────────

CMD="${1:-all}"

case "$CMD" in
    secrets)
        echo "🔑 Setting secrets for all nodes..."
        for app in "${APPS[@]}"; do
            set_secrets "$app"
        done
        ;;
    
    restart)
        echo "🔄 Restarting all nodes..."
        for app in "${APPS[@]}"; do
            restart_app "$app"
        done
        ;;
    
    alpha)
        set_secrets "$ALPHA_APP"
        cd nodes/alpha
        $FLY deploy --app "$ALPHA_APP" --config fly.toml --remote-only --detach
        echo "✅ Alpha deployed"
        ;;
    
    beta)
        set_secrets "$BETA_APP"
        cd nodes/beta
        $FLY deploy --app "$BETA_APP" --config fly.toml --remote-only --detach
        echo "✅ Beta deployed"
        ;;
    
    brain)
        set_secrets "$BRAIN_APP"
        cp -r mesh nodes/brain/
        cd nodes/brain
        $FLY deploy --app "$BRAIN_APP" --config fly.toml --dockerfile Dockerfile.brain --remote-only --detach
        echo "✅ Brain deployed"
        ;;
    
    all|*)
        echo "🚀 EVEZ OpenClaw Mesh — Full Deployment"
        echo "======================================="
        
        # 1. Set secrets first
        for app in "${APPS[@]}"; do
            set_secrets "$app"
        done
        
        # 2. Deploy brain first (it's the coordinator)
        echo ""
        echo "📡 Deploying mesh brain..."
        cp -r mesh nodes/brain/ 2>/dev/null || true
        (cd nodes/brain && $FLY deploy --app "$BRAIN_APP" --config fly.toml --dockerfile Dockerfile.brain --remote-only --detach 2>&1 | tail -5) || echo "⚠️  Brain deploy failed (may already be running)"
        
        # 3. Deploy alpha and beta in parallel
        echo ""
        echo "📡 Deploying alpha and beta nodes..."
        (cd nodes/alpha && $FLY deploy --app "$ALPHA_APP" --config fly.toml --remote-only --detach 2>&1 | tail -5 && echo "✅ Alpha deployed") &
        (cd nodes/beta  && $FLY deploy --app "$BETA_APP"  --config fly.toml --remote-only --detach 2>&1 | tail -5 && echo "✅ Beta deployed") &
        wait
        
        echo ""
        echo "⏳ Waiting 30s for machines to start..."
        sleep 30
        
        # 4. Run tests
        echo ""
        echo "🔬 Running test suite..."
        python3 mesh_orchestrator.py test || echo "⚠️  Tests failed — machines may still be starting"
        
        echo ""
        echo "============================================="
        echo "✅ EVEZ OpenClaw Mesh deployment complete"
        echo "  Alpha:  https://$ALPHA_APP.fly.dev"
        echo "  Beta:   https://$BETA_APP.fly.dev"
        echo "  Brain:  https://$BRAIN_APP.fly.dev"
        echo ""
        echo "  Test:   python3 mesh_orchestrator.py test"
        echo "  Status: python3 mesh_orchestrator.py status"
        echo "  Prompt: python3 mesh_orchestrator.py prompt 'Hello mesh'"
        echo "============================================="
        ;;
esac
