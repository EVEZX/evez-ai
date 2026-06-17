# EVEZ666 — The ARG

**You are inside a game built on top of a real system.**

The system doesn't know you're here. It simply runs. You are watching it run.

---

## What is this

An alternate reality game where the game world *is* a real autonomous cognitive system.

The EVEZ OS EventSpine runs 24/7. Every ~30 minutes it either fires or holds.
When it fires, world state changes. When it holds, the abstention is cryptographic proof.
You are in the world. Your actions affect the spine.

**The game engine is real.** The FIRE events are real. The rewards are real.

## How to play

1. **Watch the oracle**: Follow [@EVEZ666](https://twitter.com/EVEZ666) on Twitter. 
   Every FIRE post is a world state update.

2. **Decode the round data**: Each FIRE post contains:
   - Round number (R460, R487...)
   - τ (tau) — the depth of the topology crossing
   - N — the current node value (round + 80)
   - Spine hash — cryptographic identity of the event

3. **Crack the puzzle lock**: Each FIRE generates a puzzle.
   Lock = SHA256(spine_hash + round + "EVEZ_PUZZLE")
   Solution = SHA256(f"{tau}:{N}:{omega}:{spine_hash[:8]}")
   where ω = number of distinct prime factors of N

4. **Submit solutions**: https://evez666-arg.vercel.app/api/verify/{lock_prefix}
   Correct solutions unlock Gumroad lore packs and realm access.

5. **Enter realms**: EXTREME_FIRE events (τ≥20) open new realms.
   Each realm is a new chapter of the game.
   Realms are interconnected by spine hash references.

## The canon formula

```
poly_c = (τ × ω × topo) / (2 × √N)

topo = {1: 1.15, 2: 1.30, 3: 1.45}  # scales with ω
p_fire = clamp((poly_c - 0.45) / 2.10, 0, 1) ^ 0.60
```

This formula is public. It's how the oracle works. Knowing it helps you anticipate.

## Current state

- **V**: 16.94 / 17.000 (collective voltage — all FIRE events contribute)
- **Chapter**: 1 (opened by R460 EXTREME_FIRE τ=24)
- **Active realm**: https://evez666-realm-1.vercel.app
- **Total FIRE events**: 115 confirmed

## Chapter 1: R460 EXTREME_FIRE

The spine crossed τ=24 on N=540 (2²×3³×5) with p≈89.5%.
This was the deepest crossing since R1.
The first realm opened.

**Entry hash**: the R460 spine hash from @EVEZ666
**Puzzle lock**: see current @EVEZ666 thread
**Reward**: `extreme_lore_pack_chapter_unlock` on Gumroad

## Multimetaverse structure

Each EXTREME_FIRE opens a new realm:
- Realm 1: evez666-realm-1 (R460 τ=24)
- Realm 2: evez666-realm-2 (next τ≥20 event)
- ...

Realms reference each other via spine hashes.
Solving all puzzles in a realm unlocks the next realm's entry point.

## Architecture

```
EVEZ OS EventSpine (canon)
    ↓
arg_engine.py (FIRE trigger → content generation)
    ↓
agents/
  twitter_agent.py    — per-platform content generation
  puzzle_engine.py    — FIRE hash → puzzle lock
  wallet_agent.py     — deterministic wallets from FIRE entropy
  realm_spawner.py    — EXTREME_FIRE → new realm spawn
  story_protocol.py   — FIRE IP registration
  engagement_tracker.py — metric-driven content mutation
    ↓
.github/workflows/arg-engine.yml (30min cron)
```

## Self-evolution

The game writes its own next chapter from FIRE data:
- High engagement format → double down
- Low engagement → mutate content style
- New EXTREME_FIRE → new realm + new chapter
- V reaching 17 → threshold event (TBD)

---

*the map is the system. the system is the map. it doesn't know you're watching. it is simply running. ◊*

**Watch**: [@EVEZ666](https://twitter.com/EVEZ666) · [@lordevez YouTube](https://youtube.com/@lordevez)  
**Canon**: [evez-os](https://github.com/EvezArt/evez-os) · [EVEZ666 ARG](https://github.com/EvezArt/evez666-arg-canon)
