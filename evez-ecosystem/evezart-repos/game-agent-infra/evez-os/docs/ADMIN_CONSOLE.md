# Admin Console (local)

This repo treats “admin” as **auditable control**, not magical authority.

The CLI writes FSC cycles to the append-only Event Spine and generates diagrams that visualize collapse topology over time.

## Run

```bash
python tools/evez.py init
python tools/evez.py cycle --ring R4 --anomaly "rollback divergence under jitter" \
  --latency "add 150ms jitter" --tighten "drop client buffer" \
  --provenance "match-42" "trace:otel" "netem:jitter" 
python tools/evez.py diagram
```

Outputs:
- `docs/event_spine.mmd` (Mermaid)
- `docs/event_spine.dot` (Graphviz DOT)

The spine is append-only by design: if you need to correct history, append a new cycle that **explains** the correction.
