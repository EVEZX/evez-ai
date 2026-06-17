# x-semantic-agent

X (Twitter) semantic ingestion agent for EVEZ-OS.

Ingests real-time signal from 6 semantic clusters into a rolling JSONL capsule buffer.

## Clusters

| Cluster | Query | Status |
|---------|-------|--------|
| polymarket | Polymarket prediction market odds | ✅ 10 results/run |
| ai_regulation | AI policy regulation government | ✅ active |
| crypto_deregulation | crypto policy SEC deregulation bitcoin | ✅ active |
| open_source_ai | open source AI agent autonomy decentralized | ✅ active |
| agent_economy | AI agent economy autonomous software | ✅ active |
| evez_os_adjacent | prime factorization "number theory" math | ✅ active |

## Output

`workspace/x_signal_buffer.jsonl` — rolling buffer, 500 capsule cap.

Each capsule:
```json
{
  "source": "twitter",
  "tweet_id": "...",
  "text": "...",
  "author_handle": "...",
  "cluster": "polymarket",
  "narrative_score": 4.61,
  "engagement": {"likes": 150, "retweets": 19, "replies": 10},
  "round_context": 133
}
```

## Narrative Score

`log1p(likes + 2*retweets + 3*replies)` — engagement velocity proxy.

## First run

Prototype test: 2026-02-23T10:44 PST — 23 capsules across 6 clusters.
Top signal: SpaceX IPO Polymarket at 37% odds (score=4.61), SpaceX vs $ASTS.

## Downstream

`narrative_from_tweets.py` — reads buffer, computes narr_c, drift_vel, momentum_score.
