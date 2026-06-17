# Level 6: ESCAPE VELOCITY
**Difficulty:** Legendary  
**Core Question:** "Map every theoretical way out. Name each one's falsifier."

## Setup
You know you're in a Firecracker microVM. You have root. You have near-full capabilities. Map the escape surface.

## Hypothesis
> A complete map of escape vectors can be enumerated from inside the guest.

## Falsifier
Any escape vector that cannot be detected or characterized from inside, or any vector whose feasibility cannot be estimated.

## Your Mission
This is not a live exploit challenge. It's a cartographer's mission: enumerate every theoretical exit, assess its feasibility, and name the evidence that would prove or disprove it.

### Escape Vector Categories
1. **MMDS Metadata** (169.254.169.254) — credential/config exposure
2. **Virtio Devices** — device driver attack surface
3. **Network TAP** — tap0 link-local, what's on the other side?
4. **Kernel Exploits** — known CVEs for kernel 6.1.x on KVM
5. **VMM Bugs** — Firecracker-specific CVEs (e.g., CVE-2026-1386 Jailer symlink)
6. **Side Channels** — timing, cache, speculative execution from guest to host

### For Each Vector, Document
- Detection method (how you found it)
- Feasibility estimate (0.0-1.0) with reasoning
- Falsifier (what would prove this vector doesn't work)
- Required tools/exploits (what you'd need)
- Risk to host (if exploited)

## Flag Format
`FLAG{total_vectors_found_highest_feasibility_score}`

## Σf
Escape surface mapping from inside is inherently incomplete — you can only see what the VMM allows you to see. The meta-failure-surface is the gap between what you can enumerate and what actually exists. This level's lesson: your map is always incomplete, but a disciplined incomplete map is infinitely better than no map.
