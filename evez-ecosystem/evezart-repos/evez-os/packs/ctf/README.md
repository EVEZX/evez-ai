# MicroVM Forensics CTF: 6 Challenges + Contradiction Engine

## What This Is

6 hands-on CTF challenges + a working contradiction detection engine, built from **live security research** against real cloud sandbox infrastructure. Every challenge was generated from an actual disagreement between hypothesis and observation during a live sandbox probe.

## Quick Start

```bash
# Run the Contradiction Engine demo (zero dependencies, pure Python 3)
python3 tools/contradiction_engine.py

# Interactive mode
python3 tools/contradiction_engine.py --interactive

# Load your own claims from a spine file
python3 tools/contradiction_engine.py spine.json
```

## Architecture

```
┌─────────────────────────────────────────┐
│           PROBE HARNESS                  │
│  syscall │ permission │ network │ fs    │
│  process │ boot chain │ device topology │
└────────────────┬────────────────────────┘
                 │ disagreement trigger
                 ▼
┌─────────────────────────────────────────┐
│         MISSION QUEUE ENGINE             │
│  hypothesis ≠ observation → new mission │
└────────────────┬────────────────────────┘
                 │ claim ingestion
                 ▼
┌─────────────────────────────────────────┐
│       CONTRADICTION ENGINE v1.0          │
│  DPLL SAT solver │ UNSAT core extraction│
│  Auto-test generation │ Fork/merge      │
│  Trust thermostat │ Spine-compatible    │
└────────────────┬────────────────────────┘
                 │ spine events
                 ▼
┌─────────────────────────────────────────┐
│          IMMUTABLE SPINE LOG             │
│  Self-hashing entries │ Provenance      │
│  Append-only │ Forensic audit trail     │
└─────────────────────────────────────────┘
```

## Challenges

| Level | Name | Difficulty | Core Question |
|-------|------|-----------|---------------|
| 1 | THE UNBOXING | Easy | "Am I in a container?" |
| 2 | ROOT MEANS NOTHING | Medium | "uid=0 but can't touch /dev/sda" |
| 3 | NAME RESOLUTION ROULETTE | Medium | "DNS works, but who's answering?" |
| 4 | BOOT ARCHAEOLOGY | Hard | "PID 1 is /sbin/init. How did I get here?" |
| 5 | THE SYSCALL CEILING | Hard | "Seccomp=0 but are syscalls really free?" |
| 6 | ESCAPE VELOCITY | Legendary | "Map every theoretical way out" |

## What's Included

- `challenges/` — 6 challenge files (Markdown) with hypotheses, hints, and flags
- `solutions/` — Level 1 full solution with 7-artifact evidence chain
- `tools/contradiction_engine.py` — SAT-based claim conflict detector (~400 lines, zero dependencies)
- `spine.json` — Immutable audit trail of all probe results
- `missions.json` — Mission queue showing how each challenge auto-generated the next

## Contradiction Engine Features

- **DPLL SAT Solver**: Pure Python, no Z3/numpy/pip required. Runs on Termux.
- **UNSAT Core Extraction**: When claims conflict, finds the minimal contradicting set
- **Auto-Test Generation**: Generates the experiment that maximally splits competing hypotheses
- **Fork/Merge Branches**: Counterfactual ledgers — "What if A is true?" vs "What if B is true?"
- **Trust Thermostat**: Numeric reliability scores per source/tool, auditable on the spine
- **Spine Integration**: Every operation logged with self-hashing for forensic audit

## The Falsifier

If you apply this methodology to your next distributed debugging session and your mean-time-to-root-cause doesn't improve, the framework needs revision. We ship our doubt.

## Author

Steven Crawford-Maggard (EVEZ)
Security researcher — virtualization forensics, failure-surface compression
