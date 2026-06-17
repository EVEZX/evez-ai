# Independence Tiers (1/2/3)

This project supports three levels of operational independence.

## Tier 1 — Self-auditing writer (no external access required)
**Goal:** claims are never allowed to masquerade as truth without provenance + falsifier.

**Capabilities**
- `evez.py claim` appends *claims* to the spine with a speaking-rights gate.
- `evez.py lint` detects violations.

**Definition of 'independent' (Tier 1)**
- The system can **self-enforce epistemic discipline** (truth vs theater) without operator babysitting.

## Tier 2 — Single-vantage probe agent (local machine)
**Goal:** run read-only probes against explicit targets, append artifacts, generate missions from failures.

**Capabilities**
- `evez.py probe dns|http|tls|ping`
- `evez.py watch ...` to run probes periodically
- Probe results append to `spine/EVENT_SPINE.jsonl`

**Definition of 'independent' (Tier 2)**
- The system can **sense → test → log → evaluate** from one vantage point automatically.

## Tier 3 — Multi-vantage ops organism (local + remote)
**Goal:** corroborate reality across multiple vantage points and schedule itself.

**Capabilities (scaffold)**
- Add remote vantage runners (SSH or cloud function) that execute the same probes and append results tagged with `vantage_id`.
- Add schedulers (cron/systemd) to run `watch` loops for:
  - internet health probes
  - backend health probes
  - official-alert ingestion
  - FX snapshotting (already implemented)

**Definition of 'independent' (Tier 3)**
- The system can **multi-vantage probe + anomaly trigger + episode generation** with minimal operator input.

## Operational rule (all tiers)
- Anything promoted to truth/pending must carry:
  - provenance pointer
  - falsifier
  - timestamp
