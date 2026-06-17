"""WF-02 — A011 Meme Bus.

Cron: 0 */4 * * *   (Render cron service)
Env:  GROQ_API_KEY  TWITTER_API_KEY  TWITTER_ACCESS_TOKEN  TIKTOK_ACCESS_TOKEN
      N8N_FIRE_URL  METAROM_URL

Flow: generate meme content → post to X + TikTok → poll engagement every 6h
      viral threshold (>100 likes) → FIRE_REVENUE_EVENT
"""
import os, json, time, logging, asyncio
from fastapi import APIRouter

router = APIRouter(prefix="/api/meme", tags=["a011"])
log = logging.getLogger("a011_meme_bus")

GROQ_API_KEY           = os.environ.get("GROQ_API_KEY", "")
TWITTER_API_KEY        = os.environ.get("TWITTER_API_KEY", "")
TWITTER_ACCESS_TOKEN   = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TIKTOK_ACCESS_TOKEN    = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
VIRAL_THRESHOLD        = int(os.environ.get("VIRAL_THRESHOLD", "100"))


def _fire(event: str, data: dict):
    import httpx
    url = os.environ.get("N8N_FIRE_URL", "")
    if not url: return
    try: httpx.post(url, json={"event": event, "data": data, "ts": time.time()}, timeout=5)
    except: pass


def _groq_generate(prompt: str) -> str:
    if not GROQ_API_KEY:
        return "EVEZ-OS is live. Autonomous AI on-chain. Free your stack."
    import httpx
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"model": "llama3-8b-8192",
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 120},
        timeout=20
    )
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_meme_content() -> dict:
    prompt = """Write a punchy viral tweet (under 240 chars) promoting an autonomous AI OS
called EVEZ-OS. Themes: open-source AI, agent autonomy, free tools, building the future.
No hashtag overload. Make it feel human. End with https://evez.app"""
    tweet_text = _groq_generate(prompt)
    caption_prompt = "Write a 5-word TikTok caption about autonomous AI agents."
    tiktok_caption = _groq_generate(caption_prompt)
    return {"tweet": tweet_text, "tiktok_caption": tiktok_caption, "ts": time.time()}


def post_to_twitter(text: str) -> dict:
    if not (TWITTER_API_KEY and TWITTER_ACCESS_TOKEN):
        log.warning("Twitter tokens not set — skipping post")
        return {"skipped": True, "reason": "no_tokens"}
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=os.environ.get("TWITTER_API_SECRET", ""),
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET", ""),
        )
        resp = client.create_tweet(text=text)
        tweet_id = resp.data["id"]
        log.info(f"Posted tweet {tweet_id}")
        return {"tweet_id": str(tweet_id)}
    except Exception as e:
        log.error(f"Twitter post failed: {e}")
        return {"error": str(e)}


def post_to_tiktok(caption: str) -> dict:
    if not TIKTOK_ACCESS_TOKEN:
        log.warning("TikTok token not set — skipping")
        return {"skipped": True}
    log.info(f"TikTok caption queued: {caption}")
    return {"queued": caption}


def poll_engagement(tweet_id: str) -> dict:
    if not (TWITTER_API_KEY and tweet_id):
        return {"likes": 0, "viral": False}
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=os.environ.get("TWITTER_API_SECRET", ""),
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=os.environ.get("TWITTER_ACCESS_SECRET", ""),
        )
        tweet = client.get_tweet(tweet_id, tweet_fields=["public_metrics"])
        likes = tweet.data.public_metrics.get("like_count", 0)
        viral = likes >= VIRAL_THRESHOLD
        if viral:
            _fire("FIRE_REVENUE_EVENT", {"source": "a011_viral",
                                         "tweet_id": tweet_id, "likes": likes})
        return {"tweet_id": tweet_id, "likes": likes, "viral": viral}
    except Exception as e:
        log.error(f"Engagement poll failed: {e}")
        return {"error": str(e)}


async def run_meme_cycle():
    """Entry point for Render cron service."""
    log.info("A011 Meme Bus cycle starting")
    content = generate_meme_content()
    tw = post_to_twitter(content["tweet"])
    tt = post_to_tiktok(content["tiktok_caption"])
    log.info(f"Cycle complete: tweet={tw} tiktok={tt}")
    return {"tweet": tw, "tiktok": tt, "content": content}


@router.get("/status")
def meme_status():
    return {"workflow": "a011_meme_bus", "cron": "0 */4 * * *",
            "viral_threshold": VIRAL_THRESHOLD,
            "twitter_configured": bool(TWITTER_API_KEY),
            "tiktok_configured": bool(TIKTOK_ACCESS_TOKEN),
            "ts": time.time()}


@router.post("/trigger")
async def trigger_meme_cycle():
    """Manually trigger a meme cycle."""
    result = await run_meme_cycle()
    return result
