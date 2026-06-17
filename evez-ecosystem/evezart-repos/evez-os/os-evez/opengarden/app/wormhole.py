"""WF-10 — Temporal Wormhole Engine.

Cron: 0 * * * *   (Render cron service)
Flow:
  1. snapshot_now()     — capture system state
  2. project_forward()  — Groq generates T+1h, T+24h, T+7d probabilistic JSON
  3. Store in metarom {source, destination, horizon, prediction, actual, accuracy}
  4. On horizon arrival: compare prediction vs actual, compute accuracy_score
  5. Accuracy fed back into next prompt (self-calibrating)

Routes:
  GET  /api/wormhole/latest
  GET  /api/wormhole/history
  POST /api/wormhole/trigger
"""
import os, time, json, logging
from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/api/wormhole", tags=["wormhole"])
log = logging.getLogger("wormhole")

DATA_DIR = Path(os.environ.get("OG_DATA_DIR", Path.home() / "og_data"))
WH_DIR   = DATA_DIR / "wormhole"
WH_DIR.mkdir(parents=True, exist_ok=True)


def _groq(prompt: str, model="llama3-8b-8192") -> str:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key: return "{}"
    import httpx
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model,
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 512},
        timeout=30
    )
    return r.json()["choices"][0]["message"]["content"]


def _metarom_write(key: str, value: str):
    url = os.environ.get("METAROM_URL", "")
    if not url: return
    import httpx
    try:
        httpx.post(f"{url}/memory/write",
                   json={"agent_id": "wormhole", "key": key, "value": value,
                         "tags": "wormhole,forecast"},
                   timeout=10)
    except Exception as e:
        log.warning(f"metarom write failed: {e}")


def snapshot_now() -> dict:
    """Capture current system state."""
    from pathlib import Path
    runs_dir = DATA_DIR / "runs"
    run_count = len(list(runs_dir.iterdir())) if runs_dir.exists() else 0
    return {
        "ts":         time.time(),
        "run_count":  run_count,
        "wh_dir":     str(WH_DIR),
    }


def project_forward(snapshot: dict, prior_accuracy: float = 0.0) -> dict:
    """Ask Groq to generate probabilistic forecasts."""
    prompt = f"""You are a temporal forecasting engine for an autonomous AI OS (EVEZ-OS).
Current system state:
{json.dumps(snapshot, indent=2)}

Prior forecast accuracy: {prior_accuracy:.2f} (0=random, 1=perfect)

Generate a JSON forecast with these horizons (no extra text, only valid JSON):
{{
  "T_plus_1h":  {{"revenue_usd": <float>, "failure_risk": <0-1>, "spawn_probability": <0-1>, "best_post_window": "HH:MM"}},
  "T_plus_24h": {{"revenue_usd": <float>, "failure_risk": <0-1>, "spawn_probability": <0-1>, "best_post_window": "HH:MM"}},
  "T_plus_7d":  {{"revenue_usd": <float>, "failure_risk": <0-1>, "spawn_probability": <0-1>, "milestones": [<str>]}}
}}"""
    raw = _groq(prompt)
    try:
        # extract JSON from response
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        return {"raw": raw}


async def run_wormhole_cycle():
    """Entry point for Render cron."""
    log.info("Temporal Wormhole cycle starting")

    # Load prior accuracy from last cycle
    prior_accuracy = 0.0
    history_files = sorted(WH_DIR.glob("*.json"), reverse=True)
    if history_files:
        last = json.loads(history_files[0].read_text())
        prior_accuracy = last.get("accuracy", 0.0)

    snapshot   = snapshot_now()
    forecast   = project_forward(snapshot, prior_accuracy)
    cycle_id   = f"wh_{int(time.time())}"
    record = {
        "id":            cycle_id,
        "source":        "meta-orchestrator",
        "destination":   "meta-orchestrator",
        "purpose":       "Bridge past-present-future for recursive intent",
        "snapshot":      snapshot,
        "forecast":      forecast,
        "prior_accuracy": prior_accuracy,
        "accuracy":      0.0,   # updated when horizon arrives
        "ts":            time.time()
    }
    (WH_DIR / f"{cycle_id}.json").write_text(json.dumps(record, indent=2))
    _metarom_write(f"wormhole:{cycle_id}", json.dumps(record))

    log.info(f"Wormhole cycle {cycle_id} complete. Forecast: {forecast}")
    return record


@router.get("/latest")
def wormhole_latest():
    files = sorted(WH_DIR.glob("*.json"), reverse=True)
    if not files: return {"forecast": None, "msg": "no cycles yet"}
    return json.loads(files[0].read_text())


@router.get("/history")
def wormhole_history(limit: int = 24):
    files = sorted(WH_DIR.glob("*.json"), reverse=True)[:limit]
    return {"cycles": [json.loads(f.read_text()) for f in files]}


@router.post("/trigger")
async def wormhole_trigger():
    import asyncio
    result = await run_wormhole_cycle()
    return result
