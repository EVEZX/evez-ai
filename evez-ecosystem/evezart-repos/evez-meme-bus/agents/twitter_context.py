import json, pathlib, time
from collections import Counter
from bus.events import emit_event

TWEETS_PATH = pathlib.Path("data/evez666_tweets.json")

def _distill_context(tweets: list) -> dict:
    texts = [t.get("full_text") or t.get("text") or "" for t in tweets]
    combined = " ".join(texts).lower()
    themes = []
    if "fire" in combined or "\u03c4" in combined or "poly_c" in combined:
        themes.append("FIRE_TOPOLOGY")
    if "christ" in combined or "antichrist" in combined:
        themes.append("ESCHATOLOGY")
    if "pentagon" in combined or "war" in combined or "dod" in combined:
        themes.append("WAR_STATE")
    if "topology decides" in combined:
        themes.append("TOPOLOGY_DECIDES")
    top_tokens = Counter(combined.split()).most_common(20)
    return {"themes": themes, "top_tokens": top_tokens}

def run_poll_loop(interval_sec: int = 300, window: int = 200):
    last_hash = None
    print("[TwitterContext] polling", TWEETS_PATH)
    while True:
        if TWEETS_PATH.exists():
            raw = json.loads(TWEETS_PATH.read_text(encoding="utf-8"))
            recent = raw[:window]
            h = hash(json.dumps(recent, sort_keys=True))
            if h != last_hash:
                last_hash = h
                ctx = _distill_context(recent)
                emit_event("twitter", "TWEET_CONTEXT", ctx, {"source_agent": "TwitterContextAgent"})
                print(f"[TwitterContext] emitted TWEET_CONTEXT themes={ctx['themes']}")
        time.sleep(interval_sec)

if __name__ == "__main__":
    run_poll_loop()
