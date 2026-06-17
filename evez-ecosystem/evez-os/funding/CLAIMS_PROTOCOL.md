# Claims Protocol — Projection vs Canon

Canon: `spine/FUNDING_SPINE.jsonl` (append-only)

Projection: any deck / one-pager / memo / website copy that references canon.

Rules:
- No silent edits to canon. Corrections are new spine entries with `kind=correction` referencing `replaces_claim_id`.
- Every numeric claim must carry provenance:
  source (raw export / doc), calc (query/formula), and time window.
- Every non-numeric claim must carry a falsifier (“what would change my mind?”).
- truth_plane:
  pending = estimate / assumption / unverified
  final = verified and repeatable
