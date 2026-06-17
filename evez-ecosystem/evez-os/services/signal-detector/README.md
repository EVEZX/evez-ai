# signal-detector

Self-contained EVEZ signal detection service.

**Core primitive:** `DetectB` — adaptive threshold signal detector.  
**Key equivalence:** The hyperloop fire condition `poly_c >= 0.500` is `DetectB` with `fixed_threshold=0.500` (k=0). The hyperloop IS a signal detection system.

---

## Files

| File | Purpose |
|------|---------|
| `detect_b.py` | `DetectB` class — core detector logic |
| `hyperloop_adapter.py` | Bridges hyperloop round data → signal_event |
| `app.py` | FastAPI service (POST /detect, POST /ingest/signal) |
| `test_harness.py` | R114–R129 arc replay with known fire verification |
| `requirements.txt` | Python dependencies |

---

## Quick start

```bash
# Install
pip install -r requirements.txt

# Run tests (no server needed)
python test_harness.py

# Start service
uvicorn app:app --reload --port 8001
```

---

## API

```
GET  /health
GET  /state
POST /detect
POST /ingest/signal
POST /reset
```

### POST /detect — run detect_B on a single value

```json
// Request
{
  "value": 0.501175,
  "mode": "hyperloop"
}

// Response
{
  "ok": true,
  "data": {
    "detect_B": true,
    "classification": "B",
    "confidence": 0.002350,
    "peak_threshold": 0.5,
    "fire_count": 1
  }
}
```

### POST /ingest/signal — full ingestion with metadata

```json
// Request
{
  "source": "hyperloop",
  "channel": "composite",
  "raw_value": 0.501175,
  "round": 120,
  "session_id": "sess_r120",
  "mode": "hyperloop"
}

// Response (fire event)
{
  "ok": true,
  "data": {
    "schema": "signal_event/1.0",
    "detect_B": true,
    "classification": "B",
    "round": 120,
    "fire_count": 1
  }
}
```

---

## Modes

| Mode | Config | Use case |
|------|--------|----------|
| `adaptive` | Rolling baseline, k=3.0 | General signal streams |
| `hyperloop` | Fixed threshold 0.500, k=0 | EVEZ round fire detection |

---

## Test harness output (expected)

```
============================================================
EVEZ Signal Detector — R114–R129 Arc Replay
============================================================
  R114 N=66 (66=2×3×11    ) poly_c=0.570000  Δ=+0.070  FIRE      ✓
  R115 N=67 (67=PRIME     ) poly_c=0.130000  Δ=-0.370  no fire   ✓
  R116 N=68 (68=2²×17     ) poly_c=0.360000  Δ=-0.140  no fire   ✓
  R117 N=69 (69=3×23      ) poly_c=0.380000  Δ=-0.140  no fire   ✓
  R118 N=70 (70=2×5×7     ) poly_c=0.495000  Δ=-0.005  no fire   ✓
  R119 N=71 (71=PRIME     ) poly_c=0.140000  Δ=-0.360  no fire   ✓
  R120 N=72 (72=2³×3²     ) poly_c=0.501175  Δ=+0.001  FIRE      ✓
  R121 N=73 (73=PRIME     ) poly_c=0.150000  Δ=-0.350  no fire   ✓
  ...   (R122–R129 all no fire)                                   ✓

Fire count: 2 (expected 2)
Fire rounds: {66, 72} (expected {66, 72})

ALL TESTS PASSED
detect_B is structurally equivalent to hyperloop fire condition.
```

---

## Extending

To connect to the event bus when Ably is live:

```python
# In app.py, after detect_b fires:
if result['detect_B']:
    await ably_client.publish('signal.detect_B', result)
    await ably_client.publish('hyperloop.fire', result)
```

The `hyperloop.fire` topic (defined in `docs/architecture/EVEZ_IMPL.md`) will then trigger the video pipeline and feedback-engine simultaneously.

---

*signal-detector v1.0 — append-only. Canonical reference: docs/architecture/EVEZ_IMPL.md*
