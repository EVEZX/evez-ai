# PLAYTHROUGH (projection) — EP-20260218-122438-1

This file is a **mutable projection**. The spine events are immutable. Each step cites a `trace_id` you can grep in `spine/EVENT_SPINE.jsonl`.

## Step 1 — TLS / identity court
- trace_id: `T0e660829d415da8b`
- truth_plane: `pending`
- claim: In TLS, a failure may present as: identity court.
- falsifier: chain ok and time stable
- proposed_probe: validate chain + OCSP + time

## Step 2 — FSC / confidence outruns falsifier
- trace_id: `Tedc3c918867ed639`
- truth_plane: `pending`
- claim: In FSC, a failure may present as: confidence outruns falsifier.
- falsifier: falsifier provided; claim demoted/updated
- proposed_probe: compress narrative; demand falsifier

## Step 3 — BGP / route ghost
- trace_id: `Tea515270e08b64b3`
- truth_plane: `pending`
- claim: In BGP, a failure may present as: route ghost.
- falsifier: same AS-path + reachability from all vantages
- proposed_probe: multi-vantage traceroute

---

### HUD tail (what the prompter should watch)
- If your confidence rises, your falsifier must rise too.
- If a claim can’t be broken on purpose, it’s theater.
- The map begins when the mapper is mapped.
