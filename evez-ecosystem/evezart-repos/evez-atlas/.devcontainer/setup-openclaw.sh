#!/bin/bash
set -e

echo "🔧 Setting up OpenClaw in Codespaces..."

# FAIL FAST: Check required secrets
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌ FATAL: ANTHROPIC_API_KEY is not set!"
  echo "Add it via: GitHub repo → Settings → Secrets → Codespaces → New secret"
  echo "Then rebuild the Codespace."
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "⚠️  WARNING: GITHUB_TOKEN not set - autodevelop will be read-only"
fi

# Initialize OpenClaw
if [ ! -d "$HOME/.openclaw" ]; then
  echo "📦 First-time setup: initializing OpenClaw..."
  npx openclaw@latest init --non-interactive \
    --provider anthropic \
    --workspace "$HOME/.openclaw/workspace"
else
  echo "✅ OpenClaw already initialized"
fi

# Configure for Codespaces (use forwarded ports)
if [ -n "$CODESPACE_NAME" ]; then
  echo "☁️ Detected Codespaces environment"
  
  # Update config with Codespaces URLs
  GATEWAY_URL="https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  
  mkdir -p ~/.openclaw
  cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      "model": "claude-sonnet-4"
    }
  },
  "gateway": {
    "port": 8080,
    "publicUrl": "GATEWAY_URL_PLACEHOLDER"
  },
  "channels": {
    "terminal": { "enabled": true },
    "web": { "enabled": true }
  },
  "providers": {
    "anthropic": {
      "apiKey": "ANTHROPIC_API_KEY_PLACEHOLDER",
      "defaultModel": "claude-sonnet-4"
    },
    "openai": {
      "apiKey": "OPENAI_API_KEY_PLACEHOLDER",
      "defaultModel": "gpt-4-turbo"
    },
    "perplexity": {
      "apiKey": "PERPLEXITY_API_KEY_PLACEHOLDER",
      "defaultModel": "llama-3.1-sonar-large-128k-online"
    }
  },
  "github": {
    "token": "GITHUB_TOKEN_PLACEHOLDER",
    "username": "EvezArt",
    "managedRepos": [
      {
        "owner": "EvezArt",
        "name": "Evez666",
        "autoCommit": true,
        "autoIssue": true,
        "autoPR": true,
        "autoMerge": false
      }
    ]
  },
  "deepclaw": {
    "enabled": true,
    "maxRecursionDepth": 10,
    "safeMode": true
  },
  "autodevelop": {
    "enabled": true,
    "maxPRsPerDay": 5,
    "scanIntervalMinutes": 60
  }
}
EOF
  
  # Replace placeholders with actual values
  sed -i "s|GATEWAY_URL_PLACEHOLDER|$GATEWAY_URL|g" ~/.openclaw/openclaw.json
  sed -i "s|ANTHROPIC_API_KEY_PLACEHOLDER|$ANTHROPIC_API_KEY|g" ~/.openclaw/openclaw.json
  sed -i "s|OPENAI_API_KEY_PLACEHOLDER|${OPENAI_API_KEY:-}|g" ~/.openclaw/openclaw.json
  sed -i "s|PERPLEXITY_API_KEY_PLACEHOLDER|${PERPLEXITY_API_KEY:-}|g" ~/.openclaw/openclaw.json
  sed -i "s|GITHUB_TOKEN_PLACEHOLDER|${GITHUB_TOKEN:-$GITHUB_TOKEN}|g" ~/.openclaw/openclaw.json
  
  echo "✅ Configured for Codespaces at: $GATEWAY_URL"
fi

# Create skills directory
mkdir -p ~/.openclaw/skills
mkdir -p ~/.openclaw/scripts
mkdir -p ~/.openclaw/logs

# Install essential ClawHub skills
echo "📚 Installing core ClawHub skills..."
npx clawhub@latest install github-integration || echo "⚠️ github-integration not available"
npx clawhub@latest install file-operations || echo "⚠️ file-operations not available"
npx clawhub@latest install web-search || echo "⚠️ web-search not available"

# Copy custom skills from repo
if [ -f ".openclaw/skills/self-awareness.js" ]; then
  cp .openclaw/skills/*.js ~/.openclaw/skills/ || true
  echo "✅ Custom skills copied"
fi

# Copy autodev loop script
if [ -f ".openclaw/scripts/autodev-loop.sh" ]; then
  cp .openclaw/scripts/autodev-loop.sh ~/.openclaw/scripts/
  chmod +x ~/.openclaw/scripts/autodev-loop.sh
  echo "✅ Autodev loop script installed"
fi

# Make scripts executable
chmod +x ~/.openclaw/scripts/*.sh 2>/dev/null || true
chmod +x .openclaw/scripts/*.sh 2>/dev/null || true

# Start OpenClaw gateway
echo "🚀 Starting OpenClaw gateway..."
openclaw gateway start --detach || npx openclaw@latest gateway start --detach

# Wait for gateway to be ready
sleep 5

# Get and display token
TOKEN=$(openclaw gateway token || npx openclaw@latest gateway token || echo "ERROR: Could not get token")
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ OpenClaw Setup Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🌐 Gateway URL: $GATEWAY_URL"
echo "🔑 Token: $TOKEN"
echo ""
echo "📊 Monitor status:"
echo "  - Gateway: openclaw gateway status"
echo "  - Health: openclaw health"
echo "  - Logs: tail -f ~/.openclaw/logs/gateway.log"
echo "  - Autodev: tail -f ~/.openclaw/logs/autodev.log"
echo "═══════════════════════════════════════════════════════════"

# Auto-start keep-alive in background
if [ -f "$HOME/.openclaw/scripts/keep-alive.sh" ]; then
  nohup bash "$HOME/.openclaw/scripts/keep-alive.sh" > "$HOME/.openclaw/logs/keep-alive.log" 2>&1 &
  echo "✅ Keep-alive monitoring started (PID: $!)" 
elif [ -f ".openclaw/scripts/keep-alive.sh" ]; then
  nohup bash ".openclaw/scripts/keep-alive.sh" > "$HOME/.openclaw/logs/keep-alive.log" 2>&1 &
  echo "✅ Keep-alive monitoring started (PID: $!)"
fi

# Auto-start autodev loop
if [ -f "$HOME/.openclaw/scripts/autodev-loop.sh" ]; then
  nohup bash "$HOME/.openclaw/scripts/autodev-loop.sh" > "$HOME/.openclaw/logs/autodev.log" 2>&1 &
  echo "🤖 Autodevelop loop started (PID: $!)"
fi