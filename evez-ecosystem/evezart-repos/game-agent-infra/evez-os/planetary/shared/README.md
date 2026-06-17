# Shared — Schemas, Provenance, Policy

## Evidence Schema
```json
{
  "claim": "string",
  "source": "URL or database name",
  "retrieved_at": "ISO8601",
  "confidence": 0.0,
  "falsifier": "what would make this wrong",
  "canonical": true
}
```

## Canonical Provenance Chain
1. Raw source → fetched with URL + timestamp
2. Extracted claim → attributed to source
3. Canonicalized → truth_plane check
4. Scored → numeric output with error bars
5. Action → triggered only on CANONICAL

## Secrets Guidelines
- Never hardcode keys in repo
- Use workspace/ config files (gitignored)
- Rotate on any exposure suspicion
- Prefer read-only tokens when possible

## Tool Utilization Log Template
```
Connector | Action | Output | Value | Risk
Ably | publish evez:round | ok | realtime dashboard | low
Backendless | upsert evez_rounds | ok | spine persistence | low
Twitter | post video reply | tweet_id | public signal | medium
GitHub | commit module | sha | version control | low
Perplexity | crisis ingest | CRI score | evidence base | low
```

## Status
- Schemas: DEFINED
- Provenance chain: OPERATIONAL (spine append-only since R10)
- Secrets: workspace/ pattern in use
- Tool log: per-tick in state JSON
