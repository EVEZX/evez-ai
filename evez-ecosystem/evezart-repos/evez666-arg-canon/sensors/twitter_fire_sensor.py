#!/usr/bin/env python3
"""
sensors/twitter_fire_sensor.py
Scans @EVEZ666 Twitter for FIRE event ground truth.
"""
import os, json, re, sys

def scan_evez666_for_fire() -> dict:
    bearer = os.environ.get("TWITTER_BEARER_TOKEN", "")
    if not bearer:
        return None
    try:
        import tweepy
        client = tweepy.Client(bearer_token=bearer)
        user = client.get_user(username="EVEZ666")
        if not user.data:
            return None
        tweets = client.get_users_tweets(
            id=user.data.id, max_results=10,
            tweet_fields=["created_at", "text"]
        )
        if not tweets.data:
            return None
        round_pat = re.compile(r"R(\d+)")
        tau_pat = re.compile(r"tau[=:](\d+)|\u03c4=(\d+)", re.IGNORECASE)
        n_pat = re.compile(r"N=(\d+)")
        hash_pat = re.compile(r"spine[:\s]+([0-9a-f]{16,64})", re.IGNORECASE)
        for tweet in tweets.data:
            text = tweet.text
            if any(x in text.upper() for x in ["FIRE", "EXTREME"]):
                r_match = round_pat.search(text)
                t_match = tau_pat.search(text)
                n_match = n_pat.search(text)
                h_match = hash_pat.search(text)
                round_n = int(r_match.group(1)) if r_match else 461
                tau = int(t_match.group(1) or (t_match.group(2) or '4')) if t_match else 4
                fire_type = "EXTREME_FIRE" if "EXTREME" in text.upper() else "HIGH_FIRE" if tau >= 12 else "FIRE"
                return {
                    "round": round_n, "tau": tau,
                    "N": int(n_match.group(1)) if n_match else round_n + 80,
                    "type": fire_type,
                    "spine_hash": h_match.group(1) if h_match else "",
                    "p_fire": 0.895 if fire_type == "EXTREME_FIRE" else 0.6,
                    "source": "twitter_scan", "tweet_id": str(tweet.id)
                }
    except Exception as e:
        print(f"Sensor error: {e}", file=sys.stderr)
    return None

if __name__ == "__main__":
    event = scan_evez666_for_fire()
    if event:
        print(json.dumps(event))
    else:
        sys.exit(1)
