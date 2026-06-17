# Event Spine — Module 01
## Types, hashing, canonicalization

### 6 Event Types

| Type | When | Must declare |
|------|------|--------------|
| `observation` | Raw world encounter | source, raw_value |
| `transformation` | State change | input_hash, transform_hash |
| `claim` | Consequence-bearing assertion | lane, evidence_hash, transform_hash |
| `test` | Formal uncertainty protocol | hypothesis, observable, threshold, result |
| `decision` | Permission boundary | options, chosen, rationale |
| `linkage` | Bind object to history | target_hash, relation_type |

### Three-Hash Model (claims)

```
evidence_hash  = SHA256(JCS(event excluding position fields))
event_hash     = SHA256(JCS(full event including parent chain))
transform_hash = SHA256(code + params + dep_lock + runtime)
```

### Canonicalization Steps (in order)

1. NFC normalize all strings
2. Reject NaN, Infinity
3. Strict types: int≠float≠string≠bool
4. Quantize floats: round(v, 6) HALF_EVEN, -0.0→0.0
5. Timestamps: RFC3339 Z suffix only
6. Deep-freeze (no mutation after)
7. RFC8785 JCS (sorted keys, no whitespace)
8. SHA-256 over UTF-8 bytes

### Spine Invariants

1. spine[i].parent_event_hash == spine[i-1].event_hash
2. evidence_hash reproducible from payload alone
3. event_hash reproducible only with correct parent chain
4. Any break = tampering or corruption

### What spine IS / IS NOT

| IS | IS NOT |
|----|--------|
| Append-only ledger | Database |
| Source of truth | Dashboard |
| Replayable from genesis | Mutable |
| Language-agnostic JSON | Platform-dependent |