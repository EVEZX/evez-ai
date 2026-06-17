---
name: evez-fire-correlator
version: 1.0.0
description: >
  Semantic cross-correlation engine for FIRE events. Uses HuggingFace embeddings
  (sentence-transformers/all-MiniLM-L6-v2) to find cosine similarity across all
  FIRE events. Detects META-FIRE candidates when topo_overlap ≥ 0.7.
tags: [evez, fire, correlation, embeddings, meta-fire, huggingface]
---

# EVEZ FIRE Correlator

Embeds all FIRE events and finds hidden META-FIRE candidates via semantic similarity.

## What it does

1. Loads all FIRE events (from local store or Base44 entity)
2. Embeds each event's title + description + domain using `all-MiniLM-L6-v2`
3. Computes pairwise cosine similarity matrix
4. Flags pairs with similarity ≥ 0.70 as META-FIRE candidates
5. Computes candidate poly_c by merging tau, omega, N values
6. Outputs ranked candidate list

## Usage

```
/synthesize
→ Embedding 14 FIRE events...
→ Computing 91 pairwise similarities...
→ META-FIRE candidates found: 3

  [1] MPPA ↔ KoPE       similarity=0.891  candidate_poly_c=14.51  CRITICAL_MASS
  [2] DACS ↔ Kathleen   similarity=0.743  candidate_poly_c=9.03   SUPERCRITICAL
  [3] KoPE ↔ DACS       similarity=0.712  candidate_poly_c=10.98  SUPERCRITICAL
```

## Direct execution

```bash
python run.py --events-file ~/.openclaw/evez-fire-events.json
python run.py --threshold 0.65
python run.py --output mermaid
```

## Env required

```
HF_ACCESS_TOKEN=hf_...
```
