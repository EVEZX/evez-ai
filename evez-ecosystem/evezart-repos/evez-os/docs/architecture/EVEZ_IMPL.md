# EVEZ Implementation Package

**Version:** 1.0  
**Updated:** 2026-02-23  
**Status:** CANONICAL  
**Reference:** See `docs/architecture/EVEZ_STACK.md` for system blueprint

---

## 1. Folder Structure

```
evez-os/
├── spine/                          # Canonical module chain (append-only)
│   ├── watch_composite_{N}.py       # Per-composite-round modules
│   └── prime_block_watch_{K}.py     # Per-prime-block modules
├── agents/                         # Agent tracking (per-round branches)
│   └── round-{N}/
│       └── watch_composite_{N}.md
├── docs/
│   ├── architecture/
│   │   ├── EVEZ_STACK.md               # System blueprint (canonical)
│   │   └── EVEZ_IMPL.md                # This file
│   └── schemas/
│       ├── signal_event.json
│       ├── sensory_frame.json
│       ├── fused_context.json
│       ├── human_state.json
│       ├── recovery_snapshot.json
│       ├── tool_execution.json
│       └── feedback_event.json
├── services/
│   ├── claw-ui/                        # OpenClaw — interface/capture
│   ├── evez-orchestrator/              # EVEZ OS — runtime + routing
│   ├── opentree-store/                 # OpenTree — hierarchical memory
│   ├── opengraph-db/                   # OpenGraph — relationship graph
│   ├── evez-reasoner/                  # EVEZ-GPT — reasoning adapter
│   ├── media-ingest/                   # Media pipeline (YouTube/audio/vision)
│   ├── context-builder/                # Context assembly (tree+graph+vector+human)
│   ├── feedback-engine/                # Feedback capture + memory update
│   ├── signal-detector/                # Signal channel + detect_B
│   ├── sensory-fuser/                  # Sensory wheel + multimodal fusion
│   ├── human-state-model/              # Human capacity state tracking
│   └── resilience-kernel/              # Snapshot/recovery/integrity
├── evez_game/                          # Game modules (17 modules, 7400+ LOC)
├── freedom_arch/                       # Freedom architecture modules
├── planetary/                          # Crisis OS + Debt Reset + Safe AGI
├── workspace/                          # Runtime state (agent-managed)
│   ├── hyperloop_state.json
│   ├── dashboard.md
│   ├── PROMPT_QUEUE.md
│   ├── ably_config.json                # BLOCKED pending keys
│   └── backendless_config.json         # BLOCKED pending keys
├── hyperloop_state.json                # Canonical round state (root)
├── dashboard.md                        # Live status dashboard
└── CONSENT.json                        # Full operational consent record
```

---

## 2. JSON Schemas

### signal_event
```json
{
  "schema": "signal_event/1.0",
  "id": "sig_20260223_001",
  "source": "media-ingest",
  "timestamp_ms": 1740320400000,
  "channel": "classical",
  "raw_value": 0.73,
  "normalized_value": 0.73,
  "baseline_mean": 0.41,
  "baseline_std": 0.09,
  "peak_threshold": 0.68,
  "peak_detected": true,
  "decay_tau_ms": 500,
  "confidence": 0.91,
  "classification": "B",
  "detect_B": true,
  "refractory_expires_ms": 1740320400200
}
```

### sensory_frame
```json
{
  "schema": "sensory_frame/1.0",
  "id": "frame_20260223_001",
  "timestamp_ms": 1740320400000,
  "sync_window_ms": 50,
  "modalities": {
    "vision":         { "present": true,  "weight": 0.30, "feature_vec": [], "confidence": 0.87 },
    "audio":          { "present": true,  "weight": 0.30, "feature_vec": [], "confidence": 0.92 },
    "haptic":         { "present": false, "weight": 0.15, "feature_vec": [], "confidence": 0.0  },
    "proprioception": { "present": true,  "weight": 0.15, "feature_vec": [], "confidence": 0.71 },
    "interoception":  { "present": true,  "weight": 0.10, "feature_vec": [], "confidence": 0.65 }
  },
  "salience_score": 0.78,
  "fused_embedding": [],
  "watcher_flags": ["attention_spike", "audio_lead"]
}
```

### fused_context
```json
{
  "schema": "fused_context/1.0",
  "session_id": "sess_abc123",
  "round": 129,
  "assembled_at_ms": 1740320400000,
  "sources": {
    "opentree": { "nodes_retrieved": 4, "tokens_approx": 320 },
    "opengraph": { "edges_retrieved": 7, "tokens_approx": 210 },
    "vector_db": { "chunks_retrieved": 5, "tokens_approx": 480, "similarity_threshold": 0.72 },
    "human_state": { "capacity_score": 0.71, "regulation_score": 0.65, "tokens_approx": 80 },
    "signal_events": { "count": 2, "detect_B_count": 1 }
  },
  "total_tokens_approx": 1090,
  "quorum_met": true,
  "prompt_context": "[assembled prompt string]"
}
```

### human_state
```json
{
  "schema": "human_state/1.0",
  "session_id": "sess_abc123",
  "timestamp_ms": 1740320400000,
  "resource_score": 0.41,
  "regulation_score": 0.65,
  "agency_score": 0.78,
  "capacity_score": 0.71,
  "stressors": ["sleep_debt", "financial_pressure"],
  "supports": ["focused_work", "tool_augmentation"],
  "decay_rate": 0.05,
  "last_updated_ms": 1740320400000,
  "source": "inferred"
}
```

### recovery_snapshot
```json
{
  "schema": "recovery_snapshot/1.0",
  "snapshot_id": "snap_20260223_001",
  "timestamp_ms": 1740320400000,
  "trigger": "anomaly_detected",
  "state_sha256": "a3f9bc...",
  "round": 129,
  "V_global": 3.939478,
  "truth_plane": "CANONICAL",
  "integrity_checks": {
    "sha256_state": "pass",
    "round_monotonic": "pass",
    "V_global_positive": "pass"
  },
  "recovery_retries": 0,
  "status": "clean"
}
```

### tool_execution_request + result
```json
{
  "schema": "tool_execution/1.0",
  "request": {
    "id": "tool_20260223_001",
    "session_id": "sess_abc123",
    "tool": "GITHUB_COMMIT_MULTIPLE_FILES",
    "args": { "owner": "EvezArt", "repo": "evez-os", "branch": "main", "message": "...", "upserts": [] },
    "issued_at_ms": 1740320400000,
    "timeout_ms": 30000
  },
  "result": {
    "id": "tool_20260223_001",
    "success": true,
    "data": { "new_commit_sha": "087a9ea6...", "branch": "main" },
    "error": null,
    "latency_ms": 1240,
    "completed_at_ms": 1740320401240
  }
}
```

### feedback_event
```json
{
  "schema": "feedback_event/1.0",
  "id": "fb_20260223_001",
  "session_id": "sess_abc123",
  "round": 129,
  "timestamp_ms": 1740320400000,
  "type": "correction",
  "signal": "threshold_drift",
  "target": "signal-detector",
  "payload": {
    "field": "peak_threshold",
    "old_value": 0.500,
    "new_value": 0.497,
    "reason": "operator_label"
  },
  "applied": true
}
```

---

## 3. API Surfaces

### Base URL: `https://api.evez.os/v1`

| Method | Endpoint | Service | Description |
|--------|----------|---------|-------------|
| POST | `/ingest/signal` | signal-detector | Submit raw signal event for normalization + detect_B |
| POST | `/ingest/sensory` | sensory-fuser | Submit multimodal sensory frame for fusion |
| POST | `/ingest/media` | media-ingest | Submit YouTube URL / audio / video for ingestion |
| POST | `/detect` | signal-detector | Run detect_B on a pre-normalized feature vector |
| POST | `/fuse` | sensory-fuser | Fuse a set of modality inputs into unified context |
| POST | `/context/build` | context-builder | Assemble fused context for EVEZ-GPT from session_id |
| GET  | `/context/build/{session_id}` | context-builder | Retrieve last assembled context |
| POST | `/plan` | evez-orchestrator | Submit intent; returns plan + tool sequence |
| POST | `/execute` | evez-orchestrator | Execute a named tool with args |
| GET  | `/execute/{job_id}` | evez-orchestrator | Poll job status |
| GET  | `/memory/search` | context-builder | Unified search across tree+graph+vector |
| POST | `/memory/update` | opentree-store / opengraph-db | Write memory node or edge |
| POST | `/human-state/update` | human-state-model | Update operator capacity state |
| GET  | `/human-state/{session_id}` | human-state-model | Get current human state |
| POST | `/recover` | resilience-kernel | Trigger snapshot + recovery for session |
| GET  | `/recover/{snapshot_id}` | resilience-kernel | Get snapshot status |
| POST | `/feedback` | feedback-engine | Submit feedback/correction/label |
| POST | `/session` | evez-orchestrator | Create new session |
| GET  | `/session/{session_id}` | evez-orchestrator | Get session state |
| DELETE | `/session/{session_id}` | evez-orchestrator | Close session |

### Request/Response convention
```json
{
  "ok": true,
  "data": { },
  "error": null,
  "latency_ms": 0,
  "request_id": "req_..."
}
```

---

## 4. Event Bus Topics

All services communicate via an event bus (Ably / Kafka / Redis Pub-Sub).

| Topic | Publisher | Subscribers | Payload schema |
|-------|-----------|-------------|----------------|
| `signal.raw` | OpenClaw, media-ingest | signal-detector | raw sensor data |
| `signal.event` | signal-detector | context-builder, opentree-store | `signal_event` |
| `signal.detect_B` | signal-detector | evez-orchestrator, feedback-engine | `signal_event` (detect_B=true only) |
| `sensory.frame` | sensory-fuser | context-builder, opentree-store | `sensory_frame` |
| `context.ready` | context-builder | evez-reasoner | `fused_context` |
| `plan.created` | evez-orchestrator | evez-reasoner | plan object |
| `tool.request` | evez-orchestrator | all services | `tool_execution_request` |
| `tool.result` | all services | evez-orchestrator | `tool_execution_result` |
| `feedback.event` | feedback-engine | signal-detector, opentree-store, opengraph-db, human-state-model | `feedback_event` |
| `memory.update` | feedback-engine, evez-reasoner | opentree-store, opengraph-db | memory write payload |
| `human.state` | human-state-model | context-builder | `human_state` |
| `recovery.triggered` | resilience-kernel | evez-orchestrator | `recovery_snapshot` |
| `recovery.complete` | resilience-kernel | evez-orchestrator, OpenClaw | recovery result |
| `hyperloop.fire` | evez-orchestrator | media-ingest (trigger video), feedback-engine | fire event payload |
| `hyperloop.round` | evez-orchestrator | all services | round completion summary |

---

## 5. Database Tables

### Postgres (sessions, tasks, human state, logs)

```sql
-- Sessions
CREATE TABLE sessions (
    id           TEXT PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    operator_id  TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'active', -- active | closed | recovering
    state_json   JSONB
);

-- Tasks / Jobs
CREATE TABLE tasks (
    id           TEXT PRIMARY KEY,
    session_id   TEXT REFERENCES sessions(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    title        TEXT NOT NULL,
    executor     TEXT NOT NULL,           -- ai | human
    status       TEXT NOT NULL DEFAULT 'pending',
    trigger_type TEXT,                    -- cron | delay | email | null
    trigger_cfg  JSONB,
    action       TEXT,
    result_json  JSONB
);

-- Human State Log
CREATE TABLE human_state_log (
    id              BIGSERIAL PRIMARY KEY,
    session_id      TEXT REFERENCES sessions(id),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resource_score  FLOAT,
    regulation_score FLOAT,
    agency_score    FLOAT,
    capacity_score  FLOAT,
    stressors       TEXT[],
    supports        TEXT[]
);

-- Signal Events
CREATE TABLE signal_events (
    id              TEXT PRIMARY KEY,
    session_id      TEXT REFERENCES sessions(id),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel         TEXT,
    raw_value       FLOAT,
    normalized_value FLOAT,
    peak_detected   BOOLEAN,
    detect_B        BOOLEAN,
    confidence      FLOAT,
    classification  TEXT,
    payload_json    JSONB
);

-- Recovery Snapshots
CREATE TABLE recovery_snapshots (
    id              TEXT PRIMARY KEY,
    session_id      TEXT REFERENCES sessions(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    trigger         TEXT,
    state_sha256    TEXT,
    round           INT,
    V_global        FLOAT,
    integrity_json  JSONB,
    status          TEXT DEFAULT 'clean'
);

-- Feedback Events
CREATE TABLE feedback_events (
    id              TEXT PRIMARY KEY,
    session_id      TEXT REFERENCES sessions(id),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    type            TEXT,
    signal          TEXT,
    target          TEXT,
    payload_json    JSONB,
    applied         BOOLEAN DEFAULT FALSE
);
```

### OpenTree Store (Document/Hierarchy DB — Postgres JSONB or dedicated)

```sql
CREATE TABLE opentree_nodes (
    id           TEXT PRIMARY KEY,
    parent_id    TEXT REFERENCES opentree_nodes(id),
    node_type    TEXT NOT NULL,  -- Domain | Project | Session | Task | Artifact
    name         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata     JSONB,
    content      TEXT,
    embedding_id TEXT  -- FK to vector DB
);
CREATE INDEX ON opentree_nodes(parent_id);
CREATE INDEX ON opentree_nodes(node_type);
```

### OpenGraph DB (Neo4j / FalkorDB Cypher schema)

```cypher
// Nodes
CREATE (:Entity     { id: "...", name: "...", type: "...", created_at: "..." })
CREATE (:Event      { id: "...", name: "...", timestamp: "...", round: 129 })
CREATE (:Claim      { id: "...", content: "...", confidence: 0.91, source: "..." })
CREATE (:Artifact   { id: "...", path: "...", sha: "...", round: 129 })
CREATE (:Provenance { id: "...", source_url: "...", retrieved_at: "..." })

// Edges
CREATE (:Event)-[:CAUSED_BY]->(:Entity)
CREATE (:Claim)-[:SUPPORTED_BY]->(:Provenance)
CREATE (:Artifact)-[:PRODUCED_IN]->(:Event)
CREATE (:Entity)-[:RELATED_TO { weight: 0.87, type: "semantic" }]->(:Entity)
CREATE (:Event)-[:PRECEDES]->(:Event)
CREATE (:Claim)-[:CONTRADICTS { confidence: 0.62 }]->(:Claim)
```

### Vector DB (Qdrant / Weaviate / pgvector)

```
Collection: evez_embeddings
Fields:
  id:         UUID
  source:     TEXT     -- opentree_node_id | opengraph_entity_id | signal_event_id
  text:       TEXT     -- original chunk text
  embedding:  FLOAT[]  -- 1536-dim (text-embedding-3-small) or 768-dim
  round:      INT      -- hyperloop round
  modality:   TEXT     -- text | audio | vision | fused
  created_at: TIMESTAMPTZ
```

---

## 6. detect_B Pseudocode

This is the canonical EVEZ signal detection primitive. It is mathematically identical to the hyperloop fire condition: `poly_c >= 0.500` is `detect_B` with `peak_threshold = 0.500`.

```python
import math
from dataclasses import dataclass, field
from collections import deque
from typing import Optional

@dataclass
class DetectorConfig:
    k: float = 3.0                    # sigma multiplier for threshold
    decay_tau_ms: float = 500.0       # exponential decay time constant
    min_peak_prominence: float = 0.05 # min above baseline to count
    refractory_window_ms: float = 200 # lockout after detect_B fires
    baseline_window: int = 100        # samples for rolling baseline
    confidence_floor: float = 0.50    # minimum confidence to emit detect_B


class DetectB:
    """
    Adaptive threshold signal detector.
    detect_B fires when:
      normalized_value >= baseline_mean + k * baseline_std
      AND prominence >= min_peak_prominence
      AND confidence >= confidence_floor
      AND not in refractory window

    For EVEZ hyperloop: this is poly_c >= 0.500 with k=0, threshold=0.500 fixed.
    """

    def __init__(self, config: DetectorConfig = DetectorConfig()):
        self.cfg = config
        self._baseline: deque = deque(maxlen=config.baseline_window)
        self._last_fire_ms: Optional[float] = None
        self._envelope: float = 0.0   # current decay envelope

    def update_baseline(self, value: float) -> None:
        self._baseline.append(value)

    @property
    def baseline_mean(self) -> float:
        if not self._baseline:
            return 0.0
        return sum(self._baseline) / len(self._baseline)

    @property
    def baseline_std(self) -> float:
        if len(self._baseline) < 2:
            return 1.0
        m = self.baseline_mean
        variance = sum((x - m) ** 2 for x in self._baseline) / len(self._baseline)
        return math.sqrt(variance) or 1e-9

    def peak_threshold(self) -> float:
        return self.baseline_mean + self.cfg.k * self.baseline_std

    def update_envelope(self, value: float, dt_ms: float) -> float:
        """Exponential decay envelope tracker."""
        alpha = math.exp(-dt_ms / self.cfg.decay_tau_ms)
        self._envelope = max(value, self._envelope * alpha)
        return self._envelope

    def confidence(self, value: float) -> float:
        """Confidence based on distance above threshold."""
        thresh = self.peak_threshold()
        if thresh == 0:
            return 0.0
        return min(1.0, max(0.0, (value - thresh) / thresh))

    def process(self, value: float, timestamp_ms: float, dt_ms: float = 16.67) -> dict:
        """
        Process one sample. Returns signal_event dict.
        """
        self.update_baseline(value)
        envelope = self.update_envelope(value, dt_ms)
        thresh = self.peak_threshold()
        prominence = value - self.baseline_mean
        conf = self.confidence(value)

        # Refractory check
        in_refractory = (
            self._last_fire_ms is not None
            and (timestamp_ms - self._last_fire_ms) < self.cfg.refractory_window_ms
        )

        peak_detected = (
            value >= thresh
            and prominence >= self.cfg.min_peak_prominence
        )

        detect_b = (
            peak_detected
            and conf >= self.cfg.confidence_floor
            and not in_refractory
        )

        if detect_b:
            self._last_fire_ms = timestamp_ms

        # Classify A / B / C
        if detect_b:
            classification = "B"
        elif peak_detected:
            classification = "A"
        else:
            classification = "C"

        return {
            "schema": "signal_event/1.0",
            "timestamp_ms": timestamp_ms,
            "raw_value": value,
            "normalized_value": value,
            "baseline_mean": self.baseline_mean,
            "baseline_std": self.baseline_std,
            "peak_threshold": thresh,
            "envelope": envelope,
            "prominence": prominence,
            "peak_detected": peak_detected,
            "detect_B": detect_b,
            "in_refractory": in_refractory,
            "confidence": conf,
            "classification": classification,
        }


# --- EVEZ hyperloop equivalence ---
# For the hyperloop fire condition:
#   poly_c = value
#   peak_threshold = 0.500 (fixed, k=0)
#   detect_B = poly_c >= 0.500
#   refractory = next prime block round (structural minimum energy reset)
#
# Example:
#   detector = DetectB(DetectorConfig(k=0))
#   detector._baseline = deque([0.500])  # fixed threshold
#   result = detector.process(poly_c, round_number)
#   assert result['detect_B'] == (poly_c >= 0.500)
```

---

## 7. Failure Modes + Mitigations

| Failure | Mitigation |
|---------|------------|
| False positives in detect_B | Refractory window + confidence floor + prominence gate |
| Drift in decay thresholds | Rolling baseline with operator feedback loop (`feedback_event`) |
| Modality desync in sensory wheel | `sync_window_ms` alignment gate; unpresent modalities get weight=0 |
| Unstable human-state inference | Decay rate + stressor weighting; never blocks execution, only modulates context weight |
| Loop runaway / recursion traps | `EvaluateResult → NeedMoreData` capped at N iterations; max_steps enforced per agent job |
| Corrupted recovery snapshots | SHA256 checksum + round monotonicity check + V_global positivity check before reintegration |
| Graph hallucinated links | All edges require provenance node; confidence score required; stale edges expire after TTL |
| Stale memory contamination | OpenTree append-only; corrections as new dated entries (no overwrites) |
| Workbench executor death | Inline arithmetic is canonical substitute; never blocks tick; recorded in `video_render_status` |
| Probe poll timeout | Inline compute is canonical when consistent with prior rounds; recorded in `r{N}_result.note` |

---

## 8. Phase Roadmap

| Phase | Scope | Target |
|-------|-------|--------|
| **MVP** (now) | Spine (append-only modules), inline compute, GitHub commits, probe launch/poll, state JSON, dashboard | ✅ Live at R129 |
| **Alpha** | signal-detector service, context-builder, opentree-store (Postgres), vector DB, media-ingest (YouTube transcript) | R130–R145 |
| **Beta** | opengraph-db (Neo4j), sensory-fuser, human-state-model, feedback-engine, Ably event bus live | R145–R160 |
| **Scale** | OpenClaw UI, full API gateway, claw-ui web, resilience-kernel with automated snapshots, CI green across all repos | R160+ |

---

*EVEZ Implementation Package v1.0 — append-only. Corrections as new dated entries below.*
