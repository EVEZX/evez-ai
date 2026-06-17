# 🚀 Atlas v3 Complete Deployment Guide

## System Overview

Atlas v3 integrates four systems into one recursive organism:

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT SPINE (Tamper-Evident)              │
│                    SHA256 Hash Chain                         │
└────┬─────────────┬──────────────┬──────────────┬───────────┘
     │             │              │              │
     ▼             ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ ATLAS   │  │ GAME     │  │ FSC      │  │ GOVERNANCE   │
│ Kernel  │  │ Server   │  │ Monitor  │  │ Referee      │
└─────────┘  └──────────┘  └──────────┘  └──────────────┘
     │             │              │              │
     └─────────────┴──────────────┴──────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Projection Bus│
            │ (Read Models) │
            └───────────────┘
```

## Quick Start (Local)

```bash
# 1. Clone and install
git clone https://github.com/EvezArt/Evez666.git
cd Evez666
git checkout atlas-v3-kernel
npm install
pip3 install -r fsc/requirements.txt

# 2. Test recursion loop (dry run)
npm run atlas:recursion:evez666

# 3. Start HTTP spine server
npm run atlas:spine:http

# 4. (In another terminal) Run FSC experiment
python3 fsc/runner.py my_model
```

## Docker Deployment

```bash
# Start full stack
docker-compose up -d

# View spine logs
docker-compose logs -f atlas-spine

# Trigger FSC experiment
docker-compose run fsc-runner python3 /app/fsc/runner.py my_model

# Check spine integrity
curl http://localhost:7777/verify

# View projections
curl http://localhost:7777/projections
curl http://localhost:7777/projections/fsc
curl http://localhost:7777/projections/game
```

## System Components

### A. Atlas Kernel (Recursion Loop)

**Purpose**: Self-evolving code that proposes patches, verifies them, and collapses to optimal via quantum-inspired scoring.

**Files**:
- `circuit/event-spine/event-spine.ts`
- `circuit/quantum-bridge/quantum-bridge.ts`
- `circuit/recursion-loop/recursion-loop.ts`
- `circuit/projection-bus/projection-bus.ts`

**CLI**:
```bash
ATLAS_TARGET=Evez666 ATLAS_INVARIANTS='coverage>0.8,no_blind_spots' npm run atlas:recursion
```

**Invariants** (defined in `circuit/schemas/project-manifest.json`):
- `coverage>0.8` - Code coverage must exceed 80%
- `no_blind_spots` - All failure surfaces must be instrumented
- `no_console_log` - No debug logs in production

### B. Game Infrastructure

**Purpose**: Authoritative game server with client prediction + rollback (retrocausal-safe netcode).

**Files**:
- `game/server.ts` - Authoritative state + tick loop
- `game/client-bridge.ts` - Client prediction reconciliation

**Event Flow**:
```
Client predicts → Server finalizes → Mismatch? → Rollback → Re-sim from spine
                                                           ↓
                                                    Event logged
```

**Integration**:
```typescript
import { EventSpine } from "./circuit/event-spine/event-spine";
import { AuthoritativeGameServer } from "./game/server";

const spine = new EventSpine();
const gameServer = new AuthoritativeGameServer(spine, "match_001");

gameServer.addPlayer("player1");
gameServer.processInput("player1", { dx: 1, dy: 0 });
gameServer.tick();

// Rollback example
gameServer.rollback(gameServer.getState().tick - 5);
```

### C. FSC (Failure-Surface Cartography)

**Purpose**: Map model breaking points by systematic compression (prune/quantize/ablate).

**Files**:
- `fsc/runner.py` - Experiment runner

**Usage**:
```bash
ATLAS_URL=http://localhost:7777 python3 fsc/runner.py my_model
```

**Events Logged**:
- `EXPERIMENT_START` - Begin FSC run
- `PRUNE_STEP` - Each compression step + accuracy
- `COLLAPSE_DETECTED` - Failure surface Σf crossed
- `EXPERIMENT_END` - Final collapse point

**Extension**: Replace stub compression with real PyTorch/TensorFlow pruning:
```python
import torch
import torch.nn.utils.prune as prune

def prune_model(model, ratio):
    for module in model.modules():
        if isinstance(module, torch.nn.Conv2d):
            prune.l1_unstructured(module, name='weight', amount=ratio)
    return model
```

### D. Anti-Gaming Referee

**Purpose**: Multi-view verification + randomized challenges to prevent metric gaming.

**Files**:
- `referee/multi-view.ts` - Cross-source consistency checks
- `referee/challenge-engine.ts` - Surprise capability tests

**Usage**:
```typescript
import { MultiViewVerifier } from "./referee/multi-view";
import { ChallengeEngine } from "./referee/challenge-engine";
import { EventSpine } from "./circuit/event-spine/event-spine";

const spine = new EventSpine();
const verifier = new MultiViewVerifier(spine);
const challenges = new ChallengeEngine(spine);

// Multi-view verification
const views = [
  { source: "ui", timestamp: "2026-02-16T09:00:00Z", data: { score: 100 } },
  { source: "telemetry", timestamp: "2026-02-16T09:00:01Z", data: { score: 100 } },
  { source: "external", timestamp: "2026-02-16T09:00:02Z", data: { score: 99 } }
];

const result = verifier.verify(views);
if (!result.consistent) {
  console.log("Gaming detected:", result.residue);
}

// Randomized challenge
const challenge = challenges.issue("agent_007", "capability");
const answer = "compute_sha256_result_here";
const passed = challenges.verify(challenge.id, answer);
```

**Anti-Gaming Rules**:
1. **Domain access requires proof of honest play**: Agents must pass challenges to maintain privileges.
2. **Multi-view triangulation**: At least 3 independent views of same reality.
3. **Surprise residue scoring**: What the agent cannot explain is suspicious.
4. **Attested event spine**: All observations are hash-chained and signed.

## Integration Workflows

### Workflow 1: FSC → Atlas Recursion

1. FSC detects collapse at 60% pruning
2. Event logged to spine: `COLLAPSE_DETECTED`
3. Projection bus aggregates failure surfaces
4. Recursion loop proposes instrumentation patches
5. PR created with label `swarm`
6. CI validates, recursion continues

### Workflow 2: Game Rollback → Referee Check

1. Client-server mismatch triggers rollback
2. Rollback event logged with provenance
3. Referee samples multi-view consistency
4. If residue detected → issue challenge
5. Challenge response logged → referee updates trust score

### Workflow 3: Autonomous Evolution

1. Builder agent proposes 3 patch hypotheses
2. Quantum bridge scores via CI/prod signals
3. Best hypothesis collapsed and materialized
4. Verifier checks invariants
5. If passing → commit, else → iterate
6. Cycle until convergence or max cycles

## API Reference

### HTTP Spine Server

Base URL: `http://localhost:7777`

#### POST /events
Append event to spine.

**Request**:
```json
{
  "domain": "game",
  "kind": "MATCH_START",
  "payload": { "matchId": "match_001" }
}
```

**Response**:
```json
{
  "success": true,
  "record": {
    "id": "uuid",
    "index": 42,
    "timestamp": "2026-02-16T09:00:00Z",
    "domain": "game",
    "kind": "MATCH_START",
    "payload": { "matchId": "match_001" },
    "prevHash": "abc123...",
    "hash": "def456..."
  }
}
```

#### GET /events
Get full event chain.

#### GET /verify
Verify spine integrity.

**Response**:
```json
{ "ok": true }
```

#### GET /projections/:domain
Get projection for specific domain (atlas, game, fsc, governance, etc.).

#### GET /projections
Get aggregate projection across all domains.

## Production Deployment

### Option 1: Vercel (UI + API)

Deploy `lord-evez` (dashboard) to Vercel:

```bash
cd ~/lord-evez
vercel
```

Set environment variables:
- `ATLAS_SPINE_URL` → your spine server URL

### Option 2: Fly.io (Spine + Game + FSC)

```bash
fly launch --name atlas-spine
fly deploy
```

### Option 3: Kubernetes

See `k8s/` directory (to be added) for manifests.

## Monitoring

### Spine Health

```bash
# Verify integrity every 5 minutes
while true; do
  curl -s http://localhost:7777/verify | jq
  sleep 300
done
```

### Projection Dashboard

Integrate with `lord-evez` dashboard:

```javascript
fetch('http://atlas-spine:7777/projections')
  .then(r => r.json())
  .then(data => {
    console.log('Last event index:', data.lastIndex);
    console.log('Domain counts:', data.domains);
  });
```

## Troubleshooting

### Issue: "hash_mismatch" in verify

**Cause**: Event spine was tampered with or corrupted.

**Solution**: Replay from last known good checkpoint or reinitialize.

### Issue: FSC runner can't connect to spine

**Cause**: Spine server not running or wrong URL.

**Solution**:
```bash
# Check spine is running
curl http://localhost:7777/events

# Set correct URL
export ATLAS_URL=http://localhost:7777
python3 fsc/runner.py test_model
```

### Issue: Recursion loop never converges

**Cause**: Invariants too strict or builder not generating viable hypotheses.

**Solution**: Relax invariants or improve builder heuristics in `circuit/recursion-loop/recursion-loop.ts`.

## Next Steps

1. **Wire GitHub MCP**: Auto-create PRs from recursion loop
2. **Deploy to production**: Choose Fly.io / Railway / k8s
3. **Integrate with LORD dashboard**: Real-time spine visualization
4. **Add WebSocket bridge**: Real-time game events
5. **Implement full FSC**: PyTorch model compression experiments
6. **Enable auto-merge**: Set `swarm` label → CI pass → merge

## Support

- GitHub Issues: [EvezArt/Evez666/issues](https://github.com/EvezArt/Evez666/issues)
- Docs: See `README-ATLAS.md`

---

**Status**: ✅ Kernel deployed and operational.
