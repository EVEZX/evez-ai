"""x_semantic_agent.py — EVEZ-OS X (Twitter) Semantic Ingestion Agent
v0.2.0 | 2026-02-23 | SureThing

ARCHITECTURE
============
Source: X API via Composio TWITTER_RECENT_SEARCH
Output: rolling JSONL buffer -> workspace/x_signal_buffer.jsonl
        capped at BUFFER_CAP (500) entries, newest kept

CAPSULE FORMAT (one JSON object per line in buffer)
----------------------------------------------------
{
  "source":          "twitter",
  "tweet_id":        "...",
  "text":            "...",
  "author_id":       "...",
  "author_handle":   "...",
  "created_at":      "ISO8601",
  "engagement":      {"likes": N, "retweets": N, "replies": N},
  "cluster":         "polymarket|ai_regulation|crypto_deregulation|open_source_ai|agent_economy|evez_os_adjacent",
  "query":           "...",
  "narrative_score": float,   # log1p(likes + 2*rt + 3*replies)
  "ingested_at":     "ISO8601",
  "round_context":   N        # current hyperloop round
}

SEMANTIC QUERIES (6 clusters) -- prototype-validated 2026-02-23
---------------------------------------------------------------
- polymarket:         high signal (10 results per run)
- ai_regulation:      medium signal
- crypto_deregulation: broadened to capture policy discourse
- open_source_ai:     real agent economy content
- agent_economy:      broader AI agent space
- evez_os_adjacent:   number theory / math adjacent

NARRATIVE SCORE
---------------
narrative_score = log1p(likes + 2*retweets + 3*replies)
Higher score = more narrative momentum / engagement velocity.

DEDUPLICATION
-------------
tweet_id checked against loaded buffer before append.

USAGE
-----
# Dump top N by narrative_score:
python3 x_semantic_agent.py --top 10

# Summarize buffer stats:
python3 x_semantic_agent.py --stats

CRON INTEGRATION
----------------
Called by hyperloop tick after spine commit. Calls run_ingest_workbench()
from within COMPOSIO_REMOTE_WORKBENCH where run_composio_tool is available.

Downstream: narrative_from_tweets.py reads buffer and computes narr_c, drift_vel, momentum_score.

TESTED: 2026-02-23T10:44 PST -- 6 clusters live, 23 capsules ingested
  polymarket: 10 | ai_regulation: 1 | open_source_ai: 2 | evez_os_adjacent: 10
"""

import json
import math
import os
import sys
import argparse
from datetime import datetime, timezone

# -- Config -------------------------------------------------------------------

WORKSPACE   = os.path.dirname(os.path.abspath(__file__))
BUFFER_PATH = os.path.join(WORKSPACE, "x_signal_buffer.jsonl")
STATE_PATH  = os.path.join(WORKSPACE, "hyperloop_state.json")
BUFFER_CAP  = 500

SEARCH_TOOL = "TWITTER_RECENT_SEARCH"

# Semantic clusters -- validated queries
QUERIES = {
    "polymarket": (
        "Polymarket prediction market odds -is:retweet lang:en"
    ),
    "ai_regulation": (
        "AI policy regulation government -is:retweet lang:en"
    ),
    "crypto_deregulation": (
        "crypto policy SEC deregulation bitcoin -is:retweet lang:en"
    ),
    "open_source_ai": (
        "open source AI agent autonomy decentralized -is:retweet lang:en"
    ),
    "agent_economy": (
        "AI agent economy autonomous software -is:retweet lang:en"
    ),
    "evez_os_adjacent": (
        "prime factorization \"number theory\" math -is:retweet lang:en"
    ),
}

MAX_RESULTS_PER_QUERY = 10


# -- Narrative Score ----------------------------------------------------------

def narrative_score(likes: int, retweets: int, replies: int) -> float:
    """Engagement velocity proxy. log1p(likes + 2*rt + 3*replies)."""
    return round(math.log1p(likes + 2 * retweets + 3 * replies), 4)


# -- Buffer I/O ---------------------------------------------------------------

def load_buffer() -> list:
    if not os.path.exists(BUFFER_PATH):
        return []
    entries = []
    with open(BUFFER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def save_buffer(entries: list) -> None:
    if len(entries) > BUFFER_CAP:
        entries = entries[-BUFFER_CAP:]
    with open(BUFFER_PATH, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def existing_ids(entries: list) -> set:
    return {e["tweet_id"] for e in entries}


# -- State --------------------------------------------------------------------

def current_round() -> int:
    try:
        with open(STATE_PATH, "r") as f:
            state = json.load(f)
        return state.get("current_round", 0)
    except Exception:
        return 0


# -- Capsule Builder ----------------------------------------------------------

def build_capsule(tweet: dict, author_handle: str, cluster: str, query: str, round_ctx: int) -> dict:
    pm       = tweet.get("public_metrics", {})
    likes    = pm.get("like_count", 0)
    retweets = pm.get("retweet_count", 0)
    replies  = pm.get("reply_count", 0)
    return {
        "source":          "twitter",
        "tweet_id":        tweet["id"],
        "text":            tweet.get("text", ""),
        "author_id":       tweet.get("author_id", ""),
        "author_handle":   author_handle,
        "created_at":      tweet.get("created_at", ""),
        "engagement":      {"likes": likes, "retweets": retweets, "replies": replies},
        "cluster":         cluster,
        "query":           query,
        "narrative_score": narrative_score(likes, retweets, replies),
        "ingested_at":     datetime.now(timezone.utc).isoformat(),
        "round_context":   round_ctx,
    }


# -- Composio Search (workbench context only) ---------------------------------

def search_cluster_via_composio(query: str, max_results: int = 10) -> list:
    """
    Called from within COMPOSIO_REMOTE_WORKBENCH via run_composio_tool.
    Returns list of (tweet_dict, author_handle) tuples.
    """
    result, error = run_composio_tool(SEARCH_TOOL, {  # noqa: F821 injected by workbench
        "query":        query,
        "max_results":  max_results,
        "tweet_fields": ["created_at", "public_metrics", "author_id"],
        "expansions":   ["author_id"],
        "user_fields":  ["username"],
        "sort_order":   "relevancy",
    })
    if error:
        print(f"  [x_semantic_agent] search error: {error}")
        return []
    data   = result.get("data", {})
    tweets = data.get("data", [])
    users  = {u["id"]: u.get("username", "") for u in data.get("includes", {}).get("users", [])}
    return [(t, users.get(t.get("author_id", ""), "")) for t in tweets]


# -- Ingest (workbench context) -----------------------------------------------

def run_ingest_workbench(test_mode: bool = False) -> dict:
    """
    Full ingest run. Must be called from COMPOSIO_REMOTE_WORKBENCH where
    run_composio_tool is available as a helper.
    """
    print(f"[x_semantic_agent] START -- {datetime.now(timezone.utc).isoformat()}")
    buffer    = load_buffer()
    seen_ids  = existing_ids(buffer)
    round_ctx = current_round()
    queries   = dict(list(QUERIES.items())[:2]) if test_mode else QUERIES
    total_new = 0
    cluster_counts = {}
    for cluster, query in queries.items():
        print(f"  [{cluster}]")
        pairs = search_cluster_via_composio(query, max_results=MAX_RESULTS_PER_QUERY)
        new_count = 0
        for tweet, handle in pairs:
            if tweet["id"] in seen_ids:
                continue
            capsule = build_capsule(tweet, handle, cluster, query, round_ctx)
            buffer.append(capsule)
            seen_ids.add(tweet["id"])
            new_count += 1
            total_new += 1
        cluster_counts[cluster] = new_count
    save_buffer(buffer)
    summary = {
        "run_at":         datetime.now(timezone.utc).isoformat(),
        "round_context":  round_ctx,
        "total_new":      total_new,
        "buffer_size":    len(buffer),
        "cluster_counts": cluster_counts,
    }
    print(f"[x_semantic_agent] DONE -- {total_new} new | buffer={len(buffer)}")
    return summary


# -- Stats + Top N ------------------------------------------------------------

def stats() -> None:
    buffer = load_buffer()
    if not buffer:
        print("Buffer is empty.")
        return
    from collections import Counter
    clusters = Counter(e["cluster"] for e in buffer)
    scores   = sorted([e["narrative_score"] for e in buffer], reverse=True)
    print(f"Buffer: {len(buffer)} entries | cap={BUFFER_CAP}")
    print(f"By cluster: {dict(clusters)}")
    print(f"Score: max={scores[0]:.2f} p50={scores[len(scores)//2]:.2f} min={scores[-1]:.2f}")


def top_n(n: int) -> None:
    buffer = load_buffer()
    ranked = sorted(buffer, key=lambda e: e.get("narrative_score", 0), reverse=True)
    print(f"Top {n} by narrative_score:")
    for i, h in enumerate(ranked[:n], 1):
        print(f"  {i:2d}. [{h['narrative_score']:.2f}] [{h['cluster']:20s}] @{h['author_handle']}: {h['text'][:80]}")


# -- CLI ----------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EVEZ-OS X Semantic Ingestion Agent v0.2.0")
    parser.add_argument("--test",  action="store_true", help="Test mode: 2 clusters only")
    parser.add_argument("--top",   type=int, default=0, help="Dump top N by narrative_score")
    parser.add_argument("--stats", action="store_true", help="Show buffer stats")
    args = parser.parse_args()
    if args.stats:
        stats()
    elif args.top > 0:
        top_n(args.top)
    else:
        print("Full ingest requires COMPOSIO_REMOTE_WORKBENCH context (run_composio_tool helper).")
        print("Use --stats or --top N to inspect the buffer standalone.")
