# evezos/ Package Architecture

**Author:** Steven Crawford-Maggard (EVEZ666)  
**Branch:** feat/evezos-package-consolidation  
**Date:** 2026-03-28  
**Replaces:** 40+ root-level `fire_*.py` and cognition `*.py` files  

---

## Why This Exists

Every `fire_approach.py`, `fire_rekindle_watch_2.py`, `post_fourth_fire.py`
was an iteration that never got refactored back into the canonical module.
This package collapses all of them into four surgical submodules with
zero functional regression and full backward compatibility.

---

## Package Map

```
evezos/
├── __init__.py            # unified import surface
├── core.py                # EVEZCore, EVEZFork (canonical spine)
├── fire/
│   └── engine.py          # FireEngine + FireCycle + FirePhase
│                          # replaces: fire_approach, fire_border, fire_horizon,
│                          #   fire_intensify, fire_peak_approach,
│                          #   fire_rekindle_watch, fire_rekindle_watch_2,
│                          #   fire_resonance_proof, fire_settling, fire_sustain,
│                          #   pre_fire_protocol, post_fire_analysis,
│                          #   post_border_analysis, post_settling,
│                          #   third_fire, fourth_fire_analysis, fourth_fire_trigger,
│                          #   post_fourth_fire, post_fourth_fire_2,
│                          #   fifth_fire, sixth_fire, sixth_fire_approach,
│                          #   seventh_fire_ignition, ceiling_zone
├── cognition/
│   └── layer.py           # CognitionLayer + CognitionState
│                          # replaces: attractor_lock, emergence_saturation,
│                          #   entropic_renewal, resonance_stability,
│                          #   narrative_coherence, narrative_momentum,
│                          #   cohere_convergence, polyphonic_coherence,
│                          #   composite_approach, prime_silence, silent_approach,
│                          #   silent_coast, silent_prime_coast, prime_coast_2,
│                          #   prox_velocity, ceiling_zone
├── bridge/
│   └── event_bridge.py    # EventBridge: agentnet ↔ spine ↔ meme-bus ↔ income loop
└── mrom/
    └── cartridge.py       # MROMCartridge: .mrom save/load/replay
```

---

## Full Income Flywheel (closed loop)

```
evez-agentnet
  AgentMemory.write()
    → bridge.emit(AGENT_MEMORY_WRITE)
      → FireEngine.run_cycle()
        → bridge.emit(FIRE_CYCLE)
          → CognitionLayer.compute()
            → bridge.emit(COGNITION_STATE)
              → evez-meme-bus MemeBus.publish()
                → bridge.emit(MEME_PUBLISHED)
                  → IncomeSignal.record()
                    → bridge.emit(INCOME_SIGNAL)
                      → MetaLearner.reweight()
                        → next FireEngine.run_cycle()
```

---

## .mrom Cartridge Format

```python
from evezos import FireEngine, MROMCartridge, MROMHeader, MROMStep

engine = FireEngine()
cycle  = engine.run_cycle(ordinal=1, N=6, tau=4, omega_k=2, V_entry=0.0)

cart = MROMCartridge(MROMHeader(
    author="EVEZ666", title="First Fire", cart_type="FIRE_SEQ"
))
cart.add_step(MROMStep(
    step_id="fire_001", step_type="fire_cycle", ordinal=1,
    inputs={"N": 6, "tau": 4, "omega_k": 2, "V_entry": 0.0},
    outputs=cycle.to_event(), events=[cycle.to_event()],
))
cart.save("first_fire.mrom")

# Anywhere with no internet:
loaded  = MROMCartridge.load("first_fire.mrom")
results = loaded.replay()
```

---

## FastAPI EventBridge (Railway free tier)

```python
from fastapi import FastAPI
from evezos.bridge import EventBridge, EventType

app    = FastAPI(title="EVEZ-OS Event Spine")
bridge = EventBridge(log_path="evez_events.jsonl")

@bridge.on(EventType.INCOME_SIGNAL)
def on_income(event):
    # feed back to MetaLearner
    pass

app.include_router(bridge.fastapi_router(), prefix="/api")
# Deploy: uvicorn main:app --host 0.0.0.0 --port 8000
```

---

> **CEILING IS A COORDINATE. NOT A WALL.**  
> **DO NOT LET STEVEN CRAWFORD-MAGGARD BECOME FORGOT.**
