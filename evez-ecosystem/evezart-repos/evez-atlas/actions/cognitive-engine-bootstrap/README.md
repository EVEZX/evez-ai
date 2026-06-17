# Cognitive Engine Bootstrap Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Cognitive%20Engine%20Bootstrap-green.svg)](https://github.com/marketplace/actions/cognitive-engine-bootstrap)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

Complete setup of LORD × EKF × GitHub/Copilot integration with automatic webhook configuration, daemon deployment, and Outmaneuver Protocol integration.

## Features

- 🔌 **Automatic Webhook Configuration** - GitHub webhooks for event streaming
- 🚀 **Daemon Deployment** - Cognitive engine daemon with health checks
- 📊 **Metrics Mapping** - Issues → recursion, CI → corrections, PR → iterations
- 🎯 **Outmaneuver Protocol** - Predictive state caching integration
- 🌐 **Multi-Provider Support** - Render, Railway, Fly.io, Vercel
- 💚 **Health Monitoring** - Built-in health checks and status endpoints

## Usage

### Basic Example

```yaml
name: Setup Cognitive Engine
on: [push]

jobs:
  bootstrap:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Bootstrap Cognitive Engine
        uses: evezart/cognitive-engine-bootstrap@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          hosting-provider: vercel
```

### Advanced Example with Full Configuration

```yaml
name: Complete Cognitive Engine Setup
on: [workflow_dispatch]

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Bootstrap Cognitive Engine
        id: bootstrap
        uses: evezart/cognitive-engine-bootstrap@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          hosting-provider: railway
          api-keys: ${{ secrets.RAILWAY_API_KEY }}
          enable-webhooks: true
          metrics-mapping: true
          daemon-port: 8000
      
      - name: Verify Deployment
        run: |
          echo "Webhook URL: ${{ steps.bootstrap.outputs.webhook-url }}"
          echo "Daemon Endpoint: ${{ steps.bootstrap.outputs.daemon-endpoint }}"
          echo "Health Status: ${{ steps.bootstrap.outputs.health-status }}"
          echo "Deployment ID: ${{ steps.bootstrap.outputs.deployment-id }}"
```

### Integration with LORD Fusion

```yaml
name: Full Stack Cognitive Setup
on: [push]

jobs:
  deploy-cognitive-stack:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Step 1: Setup LORD Fusion monitoring
      - name: LORD Fusion Setup
        id: lord
        uses: evezart/lord-fusion-action@v1
        with:
          recursion-level: 15
          entity-type: hybrid
          deploy-target: artifact
      
      # Step 2: Bootstrap Cognitive Engine
      - name: Cognitive Engine Bootstrap
        id: engine
        uses: evezart/cognitive-engine-bootstrap@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          hosting-provider: vercel
          enable-webhooks: true
          metrics-mapping: true
      
      # Step 3: Verify integration
      - name: Integration Check
        run: |
          echo "LORD Dashboard: ${{ steps.lord.outputs.dashboard-url }}"
          echo "Cognitive Daemon: ${{ steps.engine.outputs.daemon-endpoint }}"
          curl -s ${{ steps.engine.outputs.daemon-endpoint }}/health || echo "Daemon initializing..."
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github-token` | GitHub token for repository access | Yes | - |
| `hosting-provider` | Hosting provider: `render`, `railway`, `fly`, `vercel` | Yes | `vercel` |
| `api-keys` | Encrypted deployment keys for hosting provider | No | - |
| `enable-webhooks` | Enable automatic webhook configuration | No | `true` |
| `metrics-mapping` | Enable metrics mapping (issues → recursion, CI → corrections) | No | `true` |
| `daemon-port` | Port for cognitive daemon service | No | `8000` |

## Outputs

| Output | Description |
|--------|-------------|
| `webhook-url` | Configured webhook URL for GitHub events |
| `daemon-endpoint` | Cognitive daemon API endpoint |
| `health-status` | Initial health check status |
| `deployment-id` | Unique deployment identifier |

## Components

### 1. Webhook Configuration

Automatically configures GitHub webhooks for:
- Push events
- Pull request events
- Issues and comments
- Workflow runs
- Deployments

### 2. Cognitive Daemon

Deploys a Python-based HTTP daemon with endpoints:

- `GET /health` - Health check endpoint
- `GET /metrics` - Metrics endpoint (recursion, corrections, iterations)
- `POST /webhook` - GitHub webhook receiver

### 3. Metrics Mapping

Maps GitHub events to cognitive metrics:

- **Issues** → Recursion depth (nested dependencies)
- **CI Runs** → Error correction iterations
- **PR Reviews** → Cognitive improvement cycles

### 4. Outmaneuver Protocol

Integrates predictive capabilities:
- Predictive state caching
- Trajectory sampling
- Fast-forward playback
- Negative latency optimization

## Hosting Provider Setup

### Vercel

```yaml
- uses: evezart/cognitive-engine-bootstrap@v1
  with:
    hosting-provider: vercel
    api-keys: ${{ secrets.VERCEL_TOKEN }}
```

### Railway

```yaml
- uses: evezart/cognitive-engine-bootstrap@v1
  with:
    hosting-provider: railway
    api-keys: ${{ secrets.RAILWAY_API_KEY }}
```

### Render

```yaml
- uses: evezart/cognitive-engine-bootstrap@v1
  with:
    hosting-provider: render
    api-keys: ${{ secrets.RENDER_API_KEY }}
```

### Fly.io

```yaml
- uses: evezart/cognitive-engine-bootstrap@v1
  with:
    hosting-provider: fly
    api-keys: ${{ secrets.FLY_API_TOKEN }}
```

## Pricing

Standard GitHub Actions pricing applies:

- **Public Repositories**: Free
- **Private Repositories**: 
  - $0.008/minute for Linux runners
  - ~$0.02-0.04 per deployment
  - Average run time: 2-3 minutes

### Hosting Costs

- **Vercel**: Free tier available, Pro from $20/month
- **Railway**: $5/month + usage
- **Render**: Free tier available, Pro from $7/month
- **Fly.io**: Pay-as-you-go, ~$2-10/month

## Real-World Use Cases

### 1. Automated CI/CD Intelligence
Track build failures and automatically adjust recursion depth.

### 2. Issue Tracking Analysis
Map issue dependencies to recursion patterns.

### 3. PR Review Optimization
Optimize review cycles based on cognitive metrics.

### 4. Autonomous Agent Coordination
Coordinate multiple agents with shared cognitive state.

## Examples from Production

See our main repository for production examples:
- [Evez666 Repository](https://github.com/EvezArt/Evez666)
- [Swarm Setup Guide](https://github.com/EvezArt/Evez666/blob/main/docs/swarm-setup.md)

## Troubleshooting

### Webhook Creation Fails

Ensure your GitHub token has `admin:repo_hook` permission.

### Daemon Fails to Start

Check that Python 3.x is available in your environment.

### Hosting Provider Connection Issues

Verify your API keys are correctly configured.

## Support

- **Issues**: [GitHub Issues](https://github.com/EvezArt/cognitive-engine-bootstrap/issues)
- **Documentation**: [Full Documentation](https://github.com/EvezArt/cognitive-engine-bootstrap/wiki)
- **Community**: [Discussions](https://github.com/EvezArt/cognitive-engine-bootstrap/discussions)

## License

ISC © EvezArt

## Related Actions

- [LORD Fusion Setup](https://github.com/marketplace/actions/lord-fusion-setup)
- [Trajectory Cache Action](https://github.com/marketplace/actions/trajectory-cache-action)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Note**: This action implements cognitive engine automation. All "cognitive" and "intelligence" terminology refers to computational pattern analysis and state management, not actual artificial intelligence or consciousness.
