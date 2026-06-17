# 🧬 Atlas v3 Synaptic Recursion Kernel

## Architecture

```
Substrate (circuit/) → Event Spine → Projection Bus → Agents (builder/verifier)
                           ↓
                    Quantum Bridge (ψ collapse)
```

## Components

### Event Spine (`circuit/event-spine/`)
- Tamper-evident append-only log
- SHA256 hash chain
- Deterministic replay
- Domains: atlas, game, agents, fsc, governance, observability

### Quantum Bridge (`circuit/quantum-bridge/`)
- Hypothesis superposition (multiple patch candidates)
- Oracle scoring (CI/prod signals)
- Measurement/collapse to optimal patch

### Recursion Loop (`circuit/recursion-loop/`)
- **BuilderAgent**: generates patch hypotheses
- **VerifierAgent**: scores hypotheses via oracle
- **RecursionArbiter**: orchestrates cycles until convergence

### Projection Bus (`circuit/projection-bus/`)
- Read models from event spine
- Domain-specific views (observability, agents, game, etc.)

## Usage

### Local Genesis Test
```bash
npm install
npm run atlas:recursion:evez666
```

Outputs spine JSON with:
- `GENESIS_BOOTSTRAP`
- `RECURRENCE_CYCLE` (×3)
- `RECURRENCE_STOP_CONDITION`

### HTTP Spine Server (for FSC/Game integration)
```bash
npm run atlas:spine:http
```

Endpoints:
- `POST /events` - append event
- `GET /events` - get full chain
- `GET /verify` - verify chain integrity
- `GET /projections/:domain` - domain projection

## Integration Points

### B: Game Infrastructure
Game servers emit `domain: "game"` events (match start/end, rollback, etc.).

### C: FSC Monitoring
Failure-surface experiments log `domain: "fsc"` with collapse points.

### D: Anti-Gaming Referee
Referee challenges emit `domain: "governance"` with residuals/violations.

## Invariants

Defined in `circuit/schemas/project-manifest.json`:
- `coverage>0.8`
- `no_blind_spots`
- `no_console_log` (optional)

Recursion loop enforces these via verifier scoring.

## Next Steps

1. Wire BuilderAgent to GitHub MCP (auto-create PRs)
2. Wire VerifierAgent to CI signals (GitHub Actions)
3. Deploy FSC runner (Python) that POSTs to spine HTTP server
4. Deploy game infra with WebSocket → spine bridge
5. Deploy referee system with multi-view verification

---

**Status**: Kernel deployed. Ready for integration.
