#!/usr/bin/env python3
import os, json, time
from pathlib import Path

PENDING = Path("pending_tweets.json")

def post_thread():
    if not PENDING.exists(): print("No pending tweets."); return
    data = json.loads(PENDING.read_text())
    thread = data.get("thread", [])
    if not thread: return
    try:
        import tweepy
        client = tweepy.Client(consumer_key=os.environ["TWITTER_CONSUMER_KEY"], consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"], access_token=os.environ["TWITTER_ACCESS_TOKEN"], access_token_secret=os.environ["TWITTER_ACCESS_SECRET"])
    except (ImportError, KeyError) as e:
        print(f"Twitter not configured: {e}"); return
    reply_to, posted = None, []
    for i, text in enumerate(thread):
        if len(text) > 280: text = text[:277] + "..."
        kwargs = {"text": text}
        if reply_to: kwargs["in_reply_to_tweet_id"] = reply_to
        try:
            r = client.create_tweet(**kwargs)
            reply_to = r.data["id"]; posted.append(reply_to)
            print(f"  {i+1}/{len(thread)}: {reply_to}")
            time.sleep(1.5)
        except Exception as e:
            print(f"  Failed {i+1}: {e}")
    with open("posted_threads.jsonl", "a") as f:
        f.write(json.dumps({"ids": posted, "len": len(thread), "ts": time.time()}) + "\n")
    PENDING.unlink()
    print(f"Posted: {len(posted)}/{len(thread)}")

if __name__ == "__main__":
    post_thread()
