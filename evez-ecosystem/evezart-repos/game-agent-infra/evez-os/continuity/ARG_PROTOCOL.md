# ARG Protocol — Diegetic Truth without Lying

ARG mode is a *projection layer* over the immutable spine.

**Rule 1:** Never mutate `spine/EVENT_SPINE.jsonl` (truth record).
**Rule 2:** ARG content is additive, stored in `spine/ARG_SPINE.jsonl`.
**Rule 3:** Any time ARG content implies a rewrite, it must include provenance:
  - which spine entries triggered it
  - which lobby (DNS/BGP/TLS/CDN | Backend | Mixed | Quantum | FSC)
  - whether the state is Pending or Final

**Rule 4:** “Cheat codes” are not magic; they are operational access patterns:
  - additional vantages
  - additional probes
  - privileged observability
  - rollback visibility

This keeps immersion high **and** makes the system debuggable.
