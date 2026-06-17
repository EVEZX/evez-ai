# Rollback Netcode Patch (Game Agent Infra)

This patch adds a minimal deterministic rollback protocol:
- Client-side prediction
- Server authoritative snapshots with `lastProcessedSeq`
- Client rollback + re-simulation of buffered inputs

## Files
- `shared/protocol.ts` — message and state types
- `services/game-server/src/index.js` — authoritative loop + snapshot emitter
- `client/rollbackClient.ts` — reference client buffer + rollback

## Key invariants (Ω for rollback)
- deterministic applyInput (same code/params both sides)
- monotonic `seq` per player
- snapshots acknowledge `lastProcessedSeq`
- bounded rewind window (history cap)

## Key metrics (instrument these)
- rollback_rate_per_min
- avg_rewind_ticks
- divergence_norm
- rtt_ms_p95 + jitter
