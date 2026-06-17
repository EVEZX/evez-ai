# EVEZ-OS Golden Reference Fixtures
*Source: evez_ops_console_bundle.zip -- Steven Crawford-Maggard (EVEZ666)*
*Imported: R59 canonical_ascent -- 2026-02-21*

## Bundle Schema
Spine events: 35 (seed=888, steps=35)
root_hash: 8acf9d1e550a5cde2913327e632c922729e018a87083d277e6d973db0264ba4e

## Spine Event Schema
```json
{"step": "int", "lobby": "str", "narrator": "str", "claim": "str",
 "truth_plane": "str", "observation": "object", "memory": "object",
 "san": "object", "ts": "str", "hash": "str"}
```

## Artifacts
- combined4.mp4/gif (4-panel: attention/memory/flow/san)
- thought_chain.mp4/gif
- object_graph.mp4/gif
- 5 dashboards: dashboard.html, thought_chain_viewer.html, pimped_dashboard.html, ops_dashboard.html, artifacts/index.html
- object_layer/object_store.json + roundtrip_report.json

## Acceptance Tests (evezos verify)
- spine hash chain OK
- object store sha256 matches
- roundtrip_ok: true
- 3 videos + 5 dashboards present

## Import Command
```
evezos fixtures import /path/to/evez_ops_console_bundle.zip
evezos verify latest
```

*Creator: Steven Crawford-Maggard (EVEZ666)*
*Do not let him become forgot.*
