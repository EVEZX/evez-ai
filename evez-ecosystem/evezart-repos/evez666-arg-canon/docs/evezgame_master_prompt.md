# EvezGame Speedrun Master Prompt

## Full Context Load (copy-paste into any AI session)

```
You are an expert developer on the EvezGame project — a self-modifying forensic game engine
with 21 Python modules. Here is the full architecture context:

CORE MODULES (init order is MANDATORY):
1. spine.py         → Append-only hash-chained event log. Must init FIRST before any state changes.
2. quantum_rng.py   → Probability amplitude RNG. Must seed BEFORE any stochastic processes.
3. fsc.py           → Failure-surface cartography. Must load BEFORE self_building.py unlocks.
4. threat_engine.py → 6-vector attack monitor (DNS, BGP, TLS, CDN, auth, rollback). Activates before network exposure.
5. rollback_engine.py → 60Hz ticks / 20Hz snapshots / 250ms rewind window. Temporal backbone.
6. coherency_sync.py  → Quantum-secured distributed consensus. Post-quantum Byzantine fault tolerance.
7. main.py          → Central game loop. Multi-tier scheduler. Orchestrates all 15+ subsystems.

INTELLIGENCE LAYER (load after core):
- cognition_wheel.py → R1-R7 player model (Piaget + Spiral Dynamics Beige-Turquoise)
- pattern_engine.py  → Markov chains + FFT + entangled correlation detection
- self_building.py   → Runtime code mutation. ONLY unlocks after fsc.py confirms safety invariants.
- play_forever.py    → Infinite procedural forensic episode generation

SECURITY LAYER:
- psyops.py          → Honeypots, deceptive signal injection, false flag orchestration
- truth_sifter.py    → Asset obfuscation, adversarial cost maximization

OUTPUT LAYER:
- evez_voice.py      → EVEZ666 voice clone, 6 modes: Command/Deceive/Comfort/Alert/Narrate/Sing
- visualizer.py      → Animated GIF, HTML timeline viewer, quantum state dashboard
- canonical.py       → Cross-module schema enforcement and normalized data representation

SUPPORT:
- demo.py / demo_standalone.py → Full integrated showcase / isolated component testing
- __init__.py / setup.py / requirements.txt → Package wiring and dependency management

TIMING CONSTANTS (hardcoded across all modules):
- TICK_RATE = 60Hz (16.67ms frame budget — NEVER exceed)
- SNAPSHOT_RATE = 20Hz (every 3rd tick, 50ms)
- REWIND_WINDOW = 250ms (5 snapshots)
- SPINE logs every tick with predecessor hash + quantum-derived entropy

KEY RULES:
- spine.py is ground truth. All rollback operations verify against its Merkle root.
- quantum_rng.py has 3 modes: simulation / IBM Quantum+AWS Braket / hardware RNG fallback
- self_building.py mutations auto-revert via rollback if they breach FSC invariants
- cognition_wheel.py feeds play_forever.py (narrative), evez_voice.py (prosody), visualizer.py (output)
- threat_engine.py monitors rollback_engine.py itself as an attack surface (self-referential)
- psyops.py requires strict authorization audit trail before any deception operation fires

Now [INSERT YOUR TASK HERE].
```

---

## 3-Line Context Refresh (use mid-session to save tokens)

```
EvezGame context active. Init order: spine→quantum_rng→fsc→threat_engine→rollback_engine→coherency_sync→main.
Timing: 60Hz ticks / 20Hz snapshots / 250ms rewind. spine.py is Merkle-verified ground truth.
self_building.py only unlocks post-fsc.py. Task:
```

---

## Local Launch Sequence

```bash
pip install -r requirements.txt   # Qiskit/Cirq, PyCryptodome, NumPy/SciPy, asyncio
python setup.py verify            # GPU/quantum/socket capability detection
python demo_standalone.py         # Isolated smoke test — fastest proof-of-life
python demo.py                    # Full integrated demo
python main.py                    # Production
```

---

## Skip Matrix

| Module | Skip? | What breaks |
|--------|-------|-------------|
| spine.py | ❌ Never | rollback has no ground truth |
| quantum_rng.py | ⚠️ Fallback | loses info-theoretic security |
| fsc.py | ❌ Never | self_building.py disabled |
| threat_engine.py | ✅ Dev only | safe locally, required before network |
| psyops.py | ✅ Optional | active deception disabled |
| cognition_wheel.py | ✅ Optional | loses adaptive personalization |
| self_building.py | ✅ Optional | static mechanics only |
| coherency_sync.py | ✅ Single-node | only needed for distributed |
