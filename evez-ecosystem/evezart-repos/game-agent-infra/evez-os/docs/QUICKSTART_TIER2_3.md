# Quickstart: Tier 2 / Tier 3

## Tier 2 (single-vantage)
1) Init spines:
```bash
python tools/evez.py init
python tools/evez.py arg-init
```

2) Run a probe once:
```bash
python tools/evez.py probe dns --name example.com --rrtype A --append-spine
python tools/evez.py probe tls --host example.com --append-spine
python tools/evez.py probe http --url https://example.com --append-spine
```

3) Run a watch loop (Ctrl-C to stop):
```bash
python tools/evez.py watch dns --name example.com --interval 60
```

## Tier 3 (multi-vantage scaffold)
Run Tier 2 probes from *multiple* machines and tag them with a `vantage_id`.
Recommended:
- local laptop/desktop
- a cheap VPS in another region
- optionally a home connection on a different ISP

You can unify results by shipping each machine's `spine/EVENT_SPINE.jsonl` into a central aggregator (future step) or by writing them to a shared location.

## Tier 1 (self-auditing writer)
Append a claim with truth gating:
```bash
python tools/evez.py claim --text "AZ511 closure X is active" --truth-plane pending \
  --provenance "screenshot:AZ511@2026-02-17" --falsifier "AZ511 shows open" --confidence 0.7 --scope "mobility"
```

Lint recent events:
```bash
python tools/evez.py lint --limit 300 --fail
```
