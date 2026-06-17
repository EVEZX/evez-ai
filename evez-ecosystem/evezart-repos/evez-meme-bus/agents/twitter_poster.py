"""
TwitterPoster — Posts approved memes to @EVEZ666 via X API v2.
Listens for MEME_APPROVED events with rendered image paths.
Requires: TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
Auto-post mode: set AUTO_POST_MEMES=true in env. Otherwise emits MEME_QUEUED for manual review.
"""
import os, time, pathlib, json, tweepy
from bus.events import subscribe, emit_event, Event

def _get_client():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"]
    )

def _get_api_v1():
    auth = tweepy.OAuth1UserHandler(
        os.environ["TWITTER_API_KEY"], os.environ["TWITTER_API_SECRET"],
        os.environ["TWITTER_ACCESS_TOKEN"], os.environ["TWITTER_ACCESS_SECRET"]
    )
    return tweepy.API(auth)

def handle_event(ev: Event):
    # Only handles MEME_RENDERED (image file exists) or MEME_APPROVED with image_path
    if ev.domain not in ("meme", "ethics"):
        return
    if ev.kind not in ("MEME_RENDERED", "MEME_APPROVED"):
        return

    auto_post = os.getenv("AUTO_POST_MEMES", "false").lower() == "true"
    caption = ev.payload.get("caption", "")
    image_path = ev.payload.get("rendered_path") or ev.payload.get("image_path", "")
    slot = ev.payload.get("slot", "")

    # Add topology sigil
    tweet_text = f"{caption}\n\n◊ topology decides. #EVEZ"
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    if not auto_post:
        emit_event("twitter", "MEME_QUEUED", {
            "tweet_text": tweet_text,
            "image_path": image_path,
            "slot": slot,
            "reason": "AUTO_POST_MEMES not enabled"
        }, {"source_agent": "TwitterPoster"})
        print(f"[TwitterPoster] queued (manual): {tweet_text[:60]}...")
        return

    required = ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"]
    if not all(os.getenv(k) for k in required):
        print("[TwitterPoster] missing Twitter credentials — skipping post")
        emit_event("twitter", "MEME_POST_FAILED", {
            "reason": "missing credentials", "caption": caption
        }, {"source_agent": "TwitterPoster"})
        return

    try:
        media_id = None
        img = pathlib.Path(image_path)
        if img.exists() and img.suffix.lower() in (".jpg", ".jpeg", ".png"):
            api_v1 = _get_api_v1()
            media = api_v1.media_upload(filename=str(img))
            media_id = media.media_id_string

        client = _get_client()
        kwargs = {"text": tweet_text}
        if media_id:
            kwargs["media_ids"] = [media_id]
        resp = client.create_tweet(**kwargs)
        tweet_id = resp.data["id"]
        tweet_url = f"https://x.com/EVEZ666/status/{tweet_id}"

        emit_event("twitter", "MEME_POSTED", {
            "tweet_id": tweet_id,
            "tweet_url": tweet_url,
            "tweet_text": tweet_text,
            "image_path": image_path,
            "slot": slot
        }, {"source_agent": "TwitterPoster"})
        print(f"[TwitterPoster] posted: {tweet_url}")

    except Exception as e:
        print(f"[TwitterPoster] post failed: {e}")
        emit_event("twitter", "MEME_POST_FAILED", {
            "reason": str(e), "caption": caption
        }, {"source_agent": "TwitterPoster"})

def start():
    subscribe(handle_event)

if __name__ == "__main__":
    start()
    print("[TwitterPoster] AUTO_POST_MEMES =" + os.getenv("AUTO_POST_MEMES", "false"))
    while True:
        time.sleep(60)
