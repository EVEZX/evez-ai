# Genre Lock: Rollback Shooter

This repo is now **locked** to the constraints of a fast-twitch **rollback shooter**:
- **Client predicts immediately**
- **Server is authoritative**
- **Past is rewriteable in the client view** (rollback + re-sim), but never in the spine
- **Canonical truth is delayed** by RTT + reconciliation, and must be modeled explicitly

## Contract: Pending vs Final

- **Pending (client view):** anything the client predicts locally.
- **Final (server canon):** snapshots signed by the server tick.
- **Immutable (spine):** inputs, snapshots, corrections, and audit events are append-only.

If a UI element looks final while still pending, that's a lie. This genre lives or dies on that honesty.

## Fixed Timing (defaults)

- Server tick: **60 Hz** (16.666 ms)
- Snapshot rate: **20 Hz** (every 3 ticks)
- Client sim tick: **60 Hz**
- Max rewind window: **250 ms** (15 ticks @ 60 Hz)
- Input buffer: **300 ms**
- Jitter budget: **±40 ms**

All of these are configurable via env vars (server) and constructor options (client),
but the defaults are tuned for rollback shooter feel.

## Determinism Rules

Determinism is the whole religion here.

- Fixed-point math or deterministic float discipline
- Identical integration step (dt) on client and server
- No `Math.random()` in sim (use seeded RNG if you must)
- Order of operations must be stable
- State serialization must be stable (canonical key ordering)

## What the rollback loop is allowed to rewrite

- Client rendered frames
- Client local predicted state history

## What it is NOT allowed to rewrite

- Spine records (append-only)
- Server snapshots (authoritative canon)
- Audit events (bias + fairness instrumentation)

## Failure Surface probes (FSC hooks)

Push these until the system breaks; the first collapse defines Σf for this genre:

- Increase RTT while holding tick rate constant
- Inject jitter bursts while holding mean RTT constant
- Force packet loss on inputs vs on snapshots (separately)
- Increase player count to stress snapshot bandwidth
- Increase simulation complexity (colliders/projectiles) to stress determinism

## Quick start (phone-friendly)

1. Read `docs/PHONE_QUICKSTART.md`
2. Run locally (or on any machine with node):
   - `make up`
3. Open `docs/LETS_PLAY_ADMIN_NARRATION.md` for the in-world walkthrough.
