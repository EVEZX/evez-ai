# EVEZ-OS Architecture

## Core Concept

EVEZ-OS is a **Visual Cognition Layer** for AI agents. It intercepts agent 
output and renders it as tamper-evident, animated visual artifacts.

## Components

### 1. Play Forever Engine (`tools/evez.py play`)
Generates infinite forensic episodes cycling through failure lobbies:
- `DNS` — resolver trust, cache poisoning scenarios
- `BGP` — routing table manipulation, path hijacking  
- `TLS` — certificate chain verification, MITM detection
- `CDN` — edge node trust, content integrity
- `AUTH` — identity verification, session management
- `ROLLBACK` — state rewind, snapshot consistency
- `FUNDING` — resource allocation, cost attribution
- `MIXED` — cross-domain compound failures

Each step: falsifiable claim → named probe → truth-plane assignment → spine entry.

### 2. Append-Only Spine (`spine/spine.jsonl`)
JSONL event log. Each entry is SHA256-hashed. `evez.py lint` verifies integrity.
The spine is the ground truth. It never rewrites. It only appends.

### 3. Contradiction Engine
SAT-based minimal conflict detection. Finds the exact 3-claim minimal 
conflict set when hypotheses contradict observable truth planes.

### 4. Visual Cognition Artifacts
- `cognition_map.png` — lobby transition map, color-coded by failure type
- `manifest.json` — tamper-evident output manifest with `"powered_by": "EVEZ"`

## Why Append-Only?

The spine is your audit trail. If you can rewrite it, you can fabricate it.
EVEZ-OS never rewrites spine entries. This makes the cognition layer 
forensically sound — every decision is traceable, every claim is falsifiable.

## Wheel-Rooted Cognition (R1–R7)

Epistemic stages map to Piaget→Spiral Dynamics:
- R1: Sensorimotor — raw probe data
- R2: Pre-operational — pattern recognition  
- R3: Concrete operational — hypothesis formation
- R4: Formal operational — falsification testing
- R5: Post-formal — contradiction resolution
- R6: Integral — cross-domain synthesis
- R7: Transpersonal — emergent truth-plane convergence
