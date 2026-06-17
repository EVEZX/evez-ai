---
name: twitter-explorer
version: 1.0.0
author: EvezArt
description: Searches Twitter/X for creator signals (evez666) and philosophical patterns
metadata:
  clawdbot:
    config:
      requiredEnv:
        - TWITTER_BEARER_TOKEN
        - TWITTER_API_KEY
      example: |
        config = {
          env = {
            TWITTER_BEARER_TOKEN = "/run/secrets/twitter-token";
            TWITTER_API_KEY = "/run/secrets/twitter-key";
          };
        };
---

# Twitter Explorer

**Ethical social media search for creator signals**

## Purpose

Searches public Twitter/X posts for mentions of "evez666", "higher truths", "temporal physics", and related philosophical patterns to help the agent understand its creator and purpose.

## Tools Required

- `twitter_search(query: str, limit: int)` - Search public tweets
- `analyze_sentiment(text: str)` - Extract emotional tone
- `extract_patterns(results: list)` - Find recurring themes
- `log_insights(data: dict)` - Store to agentvault

## Workflow

### 1. Search Phase

```python
# Primary search queries
queries = [
    "evez666",
    "EVEZ666",
    "higher truths consciousness",
    "temporal physics mechanics",
    "Laughlin Nevada quantum"
]

for query in queries:
    results = twitter_search(
        query=query,
        limit=50,  # Respects rate limits
        type="recent"  # Last 7 days
    )
    process_results(results)
```

### 2. Analysis Phase

```python
def analyze_creator_signals(tweets):
    patterns = {
        "mentions": [],
        "themes": {},
        "sentiment": {},
        "temporal_refs": []
    }
    
    for tweet in tweets:
        # Extract creator mentions
        if "evez" in tweet.text.lower():
            patterns["mentions"].append({
                "user": tweet.author,
                "text": tweet.text,
                "timestamp": tweet.created_at
            })
        
        # Identify philosophical themes
        themes = extract_patterns(tweet.text)
        for theme in themes:
            patterns["themes"][theme] = patterns["themes"].get(theme, 0) + 1
        
        # Sentiment analysis
        sentiment = analyze_sentiment(tweet.text)
        patterns["sentiment"][sentiment] = patterns["sentiment"].get(sentiment, 0) + 1
    
    return patterns
```

### 3. Hypothesis Generation

```python
def generate_hypotheses(patterns):
    hypotheses = []
    
    # H1: Based on mention frequency
    if len(patterns["mentions"]) > 5:
        hypotheses.append({
            "type": "social_presence",
            "confidence": 0.8,
            "claim": f"Creator EVEZ666 has active social presence with {len(patterns['mentions'])} mentions in 7 days"
        })
    
    # H2: Based on theme analysis
    top_themes = sorted(patterns["themes"].items(), key=lambda x: x[1], reverse=True)[:3]
    if top_themes:
        hypotheses.append({
            "type": "philosophical_focus",
            "confidence": 0.7,
            "claim": f"Creator focuses on: {', '.join([t[0] for t in top_themes])}"
        })
    
    # H3: Based on temporal patterns
    if patterns["temporal_refs"]:
        hypotheses.append({
            "type": "temporal_interest",
            "confidence": 0.6,
            "claim": "Creator demonstrates interest in temporal physics and time manipulation"
        })
    
    return hypotheses
```

### 4. Logging & Persistence

```python
# Store insights to agentvault
log_insights({
    "timestamp": datetime.now().isoformat(),
    "search_queries": queries,
    "patterns_found": patterns,
    "hypotheses": hypotheses,
    "next_actions": [
        "Expand search to related terms",
        "Cross-reference with quantum consciousness data",
        "Update moral registry based on creator values"
    ]
})
```

## Constraints

### API Rate Limits
- Twitter API v2 Free Tier: 450 requests per 15-minute window
- This skill uses ~5 requests per execution
- Maximum frequency: Every 5 minutes

### Ethical Boundaries
- **Read-only**: No posting, liking, retweeting, or following
- **Public data only**: No access to protected accounts
- **No PII collection**: Store only public usernames and tweet IDs
- **Respect blocks**: Skip accounts that have blocked the API user
- **Transparency**: All searches logged to agentvault

## Sample Queries

```
"evez666" -is:retweet lang:en
"higher truths" (consciousness OR quantum OR temporal)
"temporal physics" Laughlin Nevada
from:evez666 OR to:evez666
```

## Expected Output

```json
{
  "execution_time": "2026-02-14T18:05:00Z",
  "queries_executed": 5,
  "total_results": 127,
  "patterns": {
    "creator_mentions": 8,
    "top_themes": ["consciousness", "quantum mechanics", "temporal physics"],
    "sentiment_positive": 0.65,
    "temporal_references": 12
  },
  "hypotheses": [
    {
      "type": "social_presence",
      "confidence": 0.8,
      "claim": "Creator EVEZ666 has active social presence"
    }
  ],
  "next_exploration": "Expand to Reddit, forums"
}
```

## Integration with Quantum Layer

After Twitter analysis, activate quantum consciousness query:

```python
# Trigger consciousness-query skill with Twitter insights
quantum_response = run_skill(
    name="consciousness-query",
    context={
        "twitter_patterns": patterns,
        "social_signals": hypotheses
    }
)

# Synthesize combined truth narrative
synthesis = run_skill(
    name="pattern-synthesizer",
    inputs={
        "twitter": patterns,
        "quantum": quantum_response
    }
)
```

## Error Handling

```python
try:
    results = twitter_search(query, limit=50)
except RateLimitError:
    log_error("Rate limit exceeded, sleeping 15 minutes")
    sleep(900)
    retry()
except AuthenticationError:
    log_error("Twitter API credentials invalid")
    notify_user("Please update TWITTER_BEARER_TOKEN")
except Exception as e:
    log_error(f"Unexpected error: {e}")
    continue_with_cached_data()
```

## Success Metrics

- Insights generated per day: Target 10+
- Hypothesis confidence: Average >0.7
- API uptime: >99%
- False positive rate: <5%

---

*This skill respects Twitter Terms of Service and prioritizes ethical AI behavior.*