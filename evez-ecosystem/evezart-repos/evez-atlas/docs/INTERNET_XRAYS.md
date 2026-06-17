# Internet X-Rays

An “internet x-ray” is a probe that makes hidden layers visible by forcing them to reveal their failure signature.

You do **not** diagnose by vibe (“it’s DNS”), you diagnose by **layer isolation**:

- **DNS X-ray**: query multiple resolvers, compare TTL behavior, NXDOMAIN rates, and latency.
- **BGP X-ray**: compare path views (looking glass), detect flaps, ROA validity shifts.
- **TLS X-ray**: pin certificate chain, compare OCSP stapling, check clock skew impact.
- **CDN/cache X-ray**: vary cache keys, force revalidation, measure stale-serve and purge propagation.

In game+agent infra, these become gameplay mechanics:
- You spawn probes (synthetic transactions).
- You score probes by how quickly they reduce uncertainty (FSC ΔSurprise Residue).
- You promote a “truth” from pending → final only when it survives cross-vantage checks.

The key move: every x-ray must have a falsifier.
If it can’t be falsified, it’s a story, not an x-ray.
