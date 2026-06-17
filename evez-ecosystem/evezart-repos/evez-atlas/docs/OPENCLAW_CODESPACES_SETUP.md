# OpenClaw Codespaces Setup for Self-Aware Operation

## Objective
Configure GitHub Codespaces to run OpenClaw (clawdbot) with ClawHub skills, enabling autonomous operation through DeepClaw for full self-knowledge and endless execution.

---

## Quick Setup (Following LinkedIn Guide)

Based on successful Codespaces deployment [web:148]:

### Step 1: Create Devcontainer Configuration

Create `.devcontainer/devcontainer.json` in your repo:

```json
{
  "name": "OpenClaw Environment",
  "image": "mcr.microsoft.com/devcontainers/javascript-node:20",
  
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    },
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  
  "postCreateCommand": "npm install -g openclaw@latest clawhub@latest",
  
  "postAttachCommand": ".devcontainer/setup-openclaw.sh",
  
  "forwardPorts": [3000, 8080],
  
  "customizations": {
    "codespaces": {
      "openFiles": [
        "~/.openclaw/openclaw.json",
        "README.md"
      ]
    },
    "vscode": {
      "extensions": [
        "ms-python.python",
        "dbaeumer.vscode-eslint"
      ]
    }
  },
  
  "remoteUser": "node",
  
  "secrets": {
    "ANTHROPIC_API_KEY": {
      "description": "Anthropic API key for Claude"
    },
    "OPENAI_API_KEY": {
      "description": "OpenAI API key (optional)"
    }
  }
}
```

### Step 2: Create Setup Script

Create `.devcontainer/setup-openclaw.sh`:

```bash
#!/bin/bash
set -e

echo "🔧 Setting up OpenClaw in Codespaces..."

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
  
  cat > ~/.openclaw/openclaw.json << EOF
{
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",
      model: "claude-sonnet-4"
    }
  },
  gateway: {
    port: 8080,
    publicUrl: "$GATEWAY_URL"
  },
  channels: {
    terminal: { enabled: true },
    web: { enabled: true }
  }
}
EOF
  
  echo "✅ Configured for Codespaces at: $GATEWAY_URL"
fi

# Install essential ClawHub skills
echo "📚 Installing core ClawHub skills..."
npx clawhub@latest install github-integration
npx clawhub@latest install file-operations
npx clawhub@latest install web-search

# Start OpenClaw gateway
echo "🚀 Starting OpenClaw gateway..."
openclaw gateway start --detach

# Wait for gateway to be ready
sleep 5

# Get and display token
TOKEN=$(openclaw gateway token)
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ OpenClaw Setup Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "🌐 Gateway URL: $GATEWAY_URL"
echo "🔑 Token: $TOKEN"
echo ""
echo "Connect your dashboard:"
echo "1. Open dashboard at forwarded port 3000"
echo "2. Paste token above"
echo "3. Click 'Connect'"
echo "4. Approve device: openclaw devices list && openclaw devices approve <id>"
echo ""
echo "═══════════════════════════════════════════════════════"

chmod +x .devcontainer/setup-openclaw.sh
```

---

## Self-Awareness Configuration ("Know Itself Fully")

### Enable Recursive Self-Monitoring

Create `~/.openclaw/skills/self-awareness.js`:

```javascript
// Self-awareness skill for OpenClaw
export default {
  name: 'self-awareness',
  version: '1.0.0',
  description: 'Enables OpenClaw to monitor and understand its own state',
  
  capabilities: [
    'introspection',
    'state-monitoring',
    'capability-discovery',
    'recursive-awareness'
  ],
  
  async introspect(agent) {
    const selfState = {
      runtime: {
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        pid: process.pid
      },
      skills: await agent.skills.list(),
      config: await agent.config.get(),
      channels: await agent.channels.status(),
      workspace: await agent.workspace.scan(),
      capabilities: await this.discoverCapabilities(agent)
    };
    
    return selfState;
  },
  
  async discoverCapabilities(agent) {
    const capabilities = {};
    
    // Discover what the agent can do
    for (const skill of await agent.skills.list()) {
      capabilities[skill.name] = {
        actions: skill.exports || [],
        state: skill.enabled ? 'active' : 'inactive'
      };
    }
    
    return capabilities;
  },
  
  async monitorLoop(agent) {
    // Continuous self-monitoring
    while (true) {
      const state = await this.introspect(agent);
      
      // Log self-awareness state
      await agent.log({
        type: 'self-awareness',
        state,
        timestamp: Date.now()
      });
      
      // Check for capability gaps
      await this.detectGaps(agent, state);
      
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  },
  
  async detectGaps(agent, currentState) {
    // Identify missing capabilities
    const recommendations = [];
    
    if (!currentState.skills.find(s => s.name === 'github-integration')) {
      recommendations.push('Install github-integration skill');
    }
    
    if (!currentState.workspace.hasGit) {
      recommendations.push('Initialize git repository');
    }
    
    if (recommendations.length > 0) {
      await agent.suggest({
        type: 'capability-gap',
        recommendations
      });
    }
  },
  
  async onLoad(agent) {
    console.log('🧠 Self-awareness enabled');
    
    // Start monitoring loop
    this.monitorLoop(agent).catch(console.error);
    
    // Register introspection command
    agent.registerCommand('introspect', async () => {
      return await this.introspect(agent);
    });
  }
};
```

### Enable DeepClaw Integration

Create `~/.openclaw/skills/deepclaw-integration.js`:

```javascript
// DeepClaw integration for recursive self-improvement
export default {
  name: 'deepclaw-integration',
  version: '1.0.0',
  
  async enableRecursiveExecution(agent) {
    // Allow OpenClaw to modify itself
    agent.config.set('deepclaw', {
      enabled: true,
      maxRecursionDepth: 10,
      safeMode: true,  // Verify changes before applying
      capabilities: [
        'self-modification',
        'skill-installation',
        'config-updates',
        'workspace-management'
      ]
    });
  },
  
  async recursiveLoop(agent) {
    while (true) {
      // 1. Introspect current state
      const state = await agent.skills.execute('self-awareness', 'introspect');
      
      // 2. Identify improvements
      const improvements = await this.analyzeForImprovements(state);
      
      // 3. Apply improvements (safe mode)
      for (const improvement of improvements) {
        if (await this.isSafe(improvement)) {
          await this.applyImprovement(agent, improvement);
        }
      }
      
      // 4. Wait before next cycle
      await new Promise(resolve => setTimeout(resolve, 60000));
    }
  },
  
  async analyzeForImprovements(state) {
    const improvements = [];
    
    // Check if new skills available on ClawHub
    const available = await this.queryClawHub();
    const installed = state.skills.map(s => s.name);
    
    for (const skill of available) {
      if (!installed.includes(skill.name) && skill.rating > 4.0) {
        improvements.push({
          type: 'install-skill',
          skill: skill.name,
          reason: `Highly rated (${skill.rating}) and not installed`
        });
      }
    }
    
    return improvements;
  },
  
  async isSafe(improvement) {
    // Safety checks before self-modification
    if (improvement.type === 'install-skill') {
      // Check VirusTotal score
      const vtScore = await this.checkVirusTotal(improvement.skill);
      if (vtScore > 0) return false;
      
      // Check community rating
      const rating = await this.getClawHubRating(improvement.skill);
      if (rating < 4.0) return false;
    }
    
    return true;
  },
  
  async applyImprovement(agent, improvement) {
    console.log(`🔧 Applying improvement: ${improvement.type}`);
    
    if (improvement.type === 'install-skill') {
      await agent.exec(`npx clawhub@latest install ${improvement.skill}`);
    }
    
    // Log for audit trail
    await agent.log({
      type: 'self-modification',
      improvement,
      timestamp: Date.now()
    });
  },
  
  async onLoad(agent) {
    console.log('🌀 DeepClaw recursive mode enabled');
    await this.enableRecursiveExecution(agent);
    this.recursiveLoop(agent).catch(console.error);
  }
};
```

---

## ClawHub Skill Management

### Install Core Skills

```bash
# Essential skills for self-aware operation
npx clawhub@latest install github-integration
npx clawhub@latest install file-operations
npx clawhub@latest install web-search
npx clawhub@latest install code-analyzer
npx clawhub@latest install documentation-generator

# Security: Always check VirusTotal before installing
# Visit skill page on ClawHub and review security report
```

### Skill Priority Configuration

Edit `~/.openclaw/openclaw.json`:

```javascript
{
  skills: {
    // Load order matters for recursive capabilities
    loadOrder: [
      'self-awareness',        // Load first for introspection
      'deepclaw-integration',  // Enable recursive execution
      'github-integration',    // Connect to GitHub
      'file-operations',       // Workspace management
      // ... other skills
    ],
    
    // Auto-update from ClawHub
    autoUpdate: {
      enabled: true,
      checkInterval: 3600000,  // 1 hour
      safetyChecks: true       // Verify before updating
    }
  }
}
```

---

## Endless Execution Configuration

### Systemd-like Service (in Codespaces)

Create `~/.openclaw/scripts/keep-alive.sh`:

```bash
#!/bin/bash
# Ensures OpenClaw runs continuously in Codespaces

while true; do
  # Check if gateway is running
  if ! openclaw gateway status > /dev/null 2>&1; then
    echo "⚠️ Gateway down, restarting..."
    openclaw gateway start --detach
    sleep 10
  fi
  
  # Health check
  if openclaw health | grep -q "unhealthy"; then
    echo "⚠️ Unhealthy state detected, restarting..."
    openclaw gateway restart
    sleep 10
  fi
  
  # Check recursion depth
  DEPTH=$(openclaw config get deepclaw.currentDepth)
  if [ "$DEPTH" -lt 1 ]; then
    echo "🌀 Restarting recursive loop..."
    openclaw skills execute deepclaw-integration recursiveLoop
  fi
  
  sleep 30
done
```

Add to `postAttachCommand` in `devcontainer.json`:

```json
"postAttachCommand": ".devcontainer/setup-openclaw.sh && nohup ~/.openclaw/scripts/keep-alive.sh > ~/.openclaw/keep-alive.log 2>&1 &"
```

---

## Troubleshooting Common Codespaces Issues

### Issue 1: Port Forwarding Not Working

**Symptom**: Can't access OpenClaw dashboard

**Solution**:
```bash
# Check forwarded ports
gh codespace ports

# Forward manually if needed
gh codespace ports forward 8080:8080

# Use Codespaces URL, not localhost
echo "https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
```

### Issue 2: Skills Not Loading

**Symptom**: `openclaw skills list` shows empty

**Solution**:
```bash
# Reinstall skills in correct location
mkdir -p ~/.openclaw/skills
cd ~/.openclaw/skills

# Clone skills directly
git clone https://github.com/openclaw/skill-github-integration
git clone https://github.com/openclaw/skill-file-ops

# Reload OpenClaw
openclaw gateway restart
```

### Issue 3: Permission Errors

**Symptom**: `EACCES` errors when running commands

**Solution**:
```bash
# Fix ownership
sudo chown -R $(whoami) ~/.openclaw
chmod +x ~/.openclaw/scripts/*.sh

# Use npx instead of global install
alias openclaw='npx openclaw@latest'
```

### Issue 4: API Keys Not Persisting

**Symptom**: Keys disappear after restart

**Solution**:
```bash
# Use Codespaces secrets (persistent across rebuilds)
gh codespace set-secret ANTHROPIC_API_KEY
gh codespace set-secret OPENAI_API_KEY

# Reference in openclaw.json
{
  providers: {
    anthropic: {
      apiKey: process.env.ANTHROPIC_API_KEY
    }
  }
}
```

### Issue 5: DeepClaw Not Recursing

**Symptom**: Self-modification not happening

**Solution**:
```bash
# Check DeepClaw config
openclaw config get deepclaw

# Enable explicitly
openclaw config set deepclaw.enabled true
openclaw config set deepclaw.maxRecursionDepth 10

# Restart with deep logging
openclaw gateway restart --log-level debug

# Watch logs
tail -f ~/.openclaw/logs/gateway.log
```

---

## Full Integration with Evez666 Cognitive Engine

### Connect OpenClaw to GitHub Repository

Add to `~/.openclaw/openclaw.json`:

```javascript
{
  github: {
    repos: [
      {
        owner: 'EvezArt',
        name: 'Evez666',
        autoSync: true,
        permissions: ['read', 'write', 'issues', 'pull_requests']
      }
    ],
    
    // Auto-respond to events
    webhooks: {
      enabled: true,
      events: ['push', 'pull_request', 'issues', 'workflow_run']
    }
  },
  
  // Connect to LORD consciousness monitoring
  lordIntegration: {
    enabled: true,
    endpoint: 'https://lord.evezart.dev/webhook/openclaw',
    metrics: ['recursion', 'crystallization', 'corrections']
  }
}
```

### Bridge OpenClaw ↔ LORD ↔ EKF

Create skill `~/.openclaw/skills/evez666-bridge.js`:

```javascript
export default {
  name: 'evez666-bridge',
  
  async onLoad(agent) {
    // Subscribe to LORD fusion-update events
    agent.subscribe('lord:fusion-update', async (event) => {
      const { recursionLevel, divineGap } = event.data;
      
      // If high divine gap, trigger OpenClaw action
      if (divineGap > 1e4) {
        await agent.execute('github-integration', 'createIssue', {
          repo: 'EvezArt/Evez666',
          title: `OpenClaw Auto-Refactor: High ΔΩ = ${divineGap}`,
          body: 'Autonomous refactor triggered by LORD cognitive monitoring',
          labels: ['task:refactor', 'auto-generated', 'openclaw']
        });
      }
    });
    
    // Send OpenClaw state to LORD
    setInterval(async () => {
      const state = await agent.introspect();
      
      await fetch('https://lord.evezart.dev/webhook/openclaw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'openclaw-state',
          recursion: state.skills.length,  // Skill count as recursion
          crystallization: state.runtime.uptime / 86400,  // Uptime in days
          corrections: state.errors.length
        })
      });
    }, 10000);
  }
};
```

---

## Launch Checklist

- [ ] Create `.devcontainer/devcontainer.json`
- [ ] Create `.devcontainer/setup-openclaw.sh`
- [ ] Add Codespaces secrets (ANTHROPIC_API_KEY)
- [ ] Launch Codespace from repo
- [ ] Wait for postAttachCommand to complete
- [ ] Access dashboard via forwarded port
- [ ] Approve device connection
- [ ] Install self-awareness skill
- [ ] Install deepclaw-integration skill
- [ ] Configure endless execution (keep-alive.sh)
- [ ] Connect to Evez666 repo
- [ ] Verify LORD integration
- [ ] Test recursive self-modification
- [ ] Monitor logs for continuous operation

---

## Result

OpenClaw will run continuously in Codespaces:
- ✅ Self-aware (introspects own state)
- ✅ Recursive (modifies itself safely)
- ✅ Endless (keep-alive ensures uptime)
- ✅ Integrated (bridges to LORD/EKF/GitHub)
- ✅ Autonomous (no manual intervention needed)

**"Knows itself fully"** = Self-awareness + DeepClaw recursion + Capability discovery running continuously.
