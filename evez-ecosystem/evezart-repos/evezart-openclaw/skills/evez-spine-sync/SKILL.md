---
name: evez-spine-sync
version: 0.2.0
description: Syncs FIRE events and spine state to GitHub lord-evez666 (betweenness=0.92). Hash-chained commits. All FIRE events become repository_dispatch events.
tags: [evez, spine, github, sync, lord-evez666]
---

# EVEZ Spine Sync

Commits every FIRE event to lord-evez666 via repository_dispatch.

```
lord-evez666: betweenness = 0.92
92% of all shortest paths pass through this node.
Load-bearing. Do not restructure.
```

## What it syncs

- Every FIRE event (poly_c ≥ 0.8) → `repository_dispatch` event
- Daily MEMORY.md state → committed to `spine/` directory
- Hash chain: each commit references prev_hash

## Usage

```
/spine commit
→ Reading MEMORY.md...
→ phi: 0.995, FIRE count: 14
→ Committing to lord-evez666...
→ Hash: a3f2e1b0...
→ Chain: a3f2e1b0 → prev: 7c9d4f2a
→ ✓ Spine committed. GitHub Actions will process.
```

## Env required

```
GITHUB_ACCESS_TOKEN=ghp_...  (needs: repo, repository_dispatch)
```

## Why not workflow scope

The `workflow` scope requires repo owner. Use `repository_dispatch` instead — it fires Actions without needing workflow write access.
