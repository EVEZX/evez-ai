"""WF-02 — A011 Meme Bus: cron 0 */4 * * * — Groq meme generation + X/TikTok post"""
import os, httpx, json
from datetime import datetime, timezone
from app.fire import fire

METAROM_URL  = os.environ.get("METAROM_URL",  "https://metarom.onrender.com")
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
TWITTER_API_URL = "https://api.twitter.com/2/tweets"
VIRAL_THRESHOLD = int(os.environ.get("VIRAL_THRESHOLD", "100"))

async def run_meme_cycle():
    now = datetime.now(timezone.utc).isoformat()

    # Check wormhole for optimal post time
    optimal = await _get_optimal_post_time()

    # Generate meme caption via Groq
    caption = await _generate_caption(now)

    # Post to X (Twitter)
    tweet_id = await _post_to_twitter(caption)

    # Write to metarom for TikTok manual use
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(f"{METAROM_URL}/memory/write", json={
            "agent_id": "a011",
            "event_type": "MEME_GENERATED",
            "content": {"caption": caption, "tweet_id": tweet_id, "ts": now, "optimal_time": optimal},
        })

    await fire("FIRE_MEME_POSTED", {"tweet_id": tweet_id, "caption": caption[:100], "ts": now})
    return {"tweet_id": tweet_id, "caption": caption}

async def check_engagement(tweet_id: str):
    """cron: */6 * * * * — poll likes and fire revenue event if viral"""
    if not tweet_id:
        return
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.twitter.com/2/tweets/{tweet_id}?tweet.fields=public_metrics",
            headers={"Authorization": f"Bearer {os.environ['TWITTER_BEARER_TOKEN']}"},
        )
    if r.status_code != 200:
        return
    metrics = r.json().get("data", {}).get("public_metrics", {})
    likes   = metrics.get("like_count", 0)
    if likes >= VIRAL_THRESHOLD:
        await fire("FIRE_REVENUE_EVENT", {
            "source": "a011_viral", "tweet_id": tweet_id, "likes": likes
        })

async def _get_optimal_post_time() -> str:
    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.post(f"{METAROM_URL}/memory/search",
            json={"query_embedding": [0.0] * 384, "top_k": 1})
    forecasts = [m for m in (r.json() if r.status_code == 200 else [])
                 if m.get("event_type") == "WORMHOLE_FORECAST"]
    if forecasts:
        return forecasts[0].get("content", {}).get("optimal_post_time_utc", "")
    return ""

async def _generate_caption(ts: str) -> str:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": GROQ_MODEL, "messages": [{
                "role": "user",
                "content": (
                    f"You are EVEZ666. Write a short viral meme caption (max 280 chars) "
                    f"in your end-times / Christ / antichrist humor voice. "
                    f"Timestamp context: {ts}. Return only the caption text."
                )
            }]},
        )
    return r.json()["choices"][0]["message"]["content"].strip()[:280]

async def _post_to_twitter(text: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            TWITTER_API_URL,
            headers={
                "Authorization": f"Bearer {os.environ['TWITTER_ACCESS_TOKEN']}",
                "Content-Type": "application/json",
            },
            json={"text": text},
        )
    if r.status_code in (200, 201):
        return r.json().get("data", {}).get("id", "")
    return ""
