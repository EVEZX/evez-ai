# 🧠 NEUROS — Free Autonomous Agent Runtime

The thing OpenClaw should have been.

**$0/month. Self-provisioning. Self-healing. Self-evolving. Distributed.**

## OpenClaw vs NEUROS

| Limitation | OpenClaw | NEUROS |
|---|---|---|
| Cost | Requires VPS ($5-20/mo) | **$0/mo forever** |
| Self-provisioning | ❌ Can't create servers | ✅ Auto-creates free VPS |
| Memory | Local files, dies with node | **Git-synced distributed mesh** |
| Multi-agent | Limited spawns | **Unlimited agents per node** |
| OAuth | ❌ Needs human at browser | ✅ **OAuthBot** automates flows |
| Model training | ❌ Can't train | ✅ **Free GPU** (Colab/Kaggle) |
| Product generation | ❌ No | ✅ **Autonomous product factory** |
| Node failure | 💀 Single point of failure | ✅ **Mesh survives N-1 failures** |
| Public URL | ❌ Needs config | ✅ **Cloudflare tunnels** (free) |
| Disk management | ❌ Manual | ✅ **Auto-cleanup** at 88% |
| Scaling | ❌ Single process | ✅ **Multi-node mesh** |

## Quick Start

```bash
# One command — bootstraps everything
bash <(curl -s https://raw.githubusercontent.com/EVEZX/neuros/main/install.sh)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health + node count |
| `/v1/agents` | POST | Spawn a new agent |
| `/v1/agents/chat` | POST | Chat with an agent |
| `/v1/memory` | POST/GET | Distributed mesh memory |
| `/v1/oauth/start` | POST | Start headless OAuth flow |
| `/v1/provision` | POST | Auto-provision free VPS |
| `/v1/providers` | GET | List free compute providers |
| `/v1/train` | POST | Create GPU training job |
| `/v1/train/platforms` | GET | List free GPU platforms |
| `/v1/products` | POST/GET | Generate & list products |
| `/v1/mesh` | GET | Mesh topology status |

## Free Compute Providers

| Provider | CPU | RAM | GPU | Cost |
|----------|-----|-----|-----|------|
| Oracle Cloud | 4 ARM | 24GB | — | $0/mo |
| Google Cloud | 0.25 | 1GB | — | $0/mo |
| Codespaces | 2 | 8GB | — | free |
| Google Colab | 2 | 12GB | T4 16GB | $0 |
| Kaggle | 4 | 30GB | P100 16GB | $0 |
| Lightning AI | — | — | A10G 24GB | $0 |

## Architecture

```
NEUROS MESH
├── AgentRuntime ── Unlimited agent spawning
├── MeshMemory  ── Git-backed distributed state
├── OAuthBot    ── Headless auth automation
├── Provisioner── Self-creates cloud instances
├── ProductGen  ── Autonomous product factory
├── ModelTrainer── Free GPU fine-tuning
└── HealthMesh  ── Cross-node monitoring
```

## License

AGPL-3.0 + Commercial (same as EVEZ-OS)

---

Built by [EVEZ](https://github.com/EVEZX) from a phone in a parking lot.
Constraint IS the design.
