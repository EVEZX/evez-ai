"""WF-10 — Temporal Wormhole Engine: cron 0 * * * * — hourly forecast + self-calibration"""
import os, httpx, json
from datetime import datetime, timezone
from app.fire import fire

METAROM_URL = os.environ.get("METAROM_URL", "https://metarom.onrender.com")
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama3-8b-8192")

async def run_wormhole_cycle():
    now = datetime.now(timezone.utc).isoformat()

    # 1. Score past predictions first
    await _score_past_predictions()

    # 2. Load recent memory context
    context = await _load_memory_context()

    # 3. Ask Groq for forecast
    prompt = (
        f"Current UTC: {now}\n"
        f"Recent system context:\n{context}\n\n"
        "Return ONLY valid JSON with these keys:\n"
        "revenue_forecast_24h (float USD), crash_probability_1h (0-1), "
        "spawn_probability_1h (0-1), optimal_post_time_utc (ISO string), "
        "confidence (0-1), reasoning (string)"
    )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]},
        )
        resp.raise_for_status()

    raw = resp.json()["choices"][0]["message"]["content"]
    forecast = json.loads(raw)
    forecast.update({
        "timestamp": now,
        "source": "temporal-wormhole",
        "destination": "meta-orchestrator",
        "purpose": "Bridge past-present-future for recursive intent",
    })

    # 4. Write to metarom
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(f"{METAROM_URL}/memory/write", json={
            "agent_id": "wormhole",
            "event_type": "WORMHOLE_FORECAST",
            "content": forecast,
        })

    await fire("FIRE_WORMHOLE_CYCLE", forecast)
    return forecast

async def _score_past_predictions():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{METAROM_URL}/memory/search",
            json={"query_embedding": [0.0] * 384, "top_k": 20})
    if resp.status_code != 200:
        return
    memories = resp.json()
    forecasts = [m for m in memories if m["event_type"] == "WORMHOLE_FORECAST"]
    crashes   = [m for m in memories if m["event_type"] == "FIRE_AGENT_CRASH"]
    if forecasts:
        accuracy = min(1.0, len(crashes) / max(1, len(forecasts)))
        await fire("FIRE_WORMHOLE_ACCURACY", {
            "accuracy_score": accuracy,
            "total_forecasts": len(forecasts),
            "actual_crashes": len(crashes),
        })

async def _load_memory_context() -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{METAROM_URL}/memory/search",
            json={"query_embedding": [0.0] * 384, "top_k": 5})
    if resp.status_code != 200:
        return "No context available"
    return "\n".join(
        f"[{m['event_type']}] {json.dumps(m['content'])[:200]}"
        for m in resp.json()
    )
