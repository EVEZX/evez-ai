#!/usr/bin/env python3
"""run_organism.py — Launch EVEZ-OS as a live daemon.

The organism. Not a script that runs and exits.
A process that senses, classifies, acts, records, falsifies, adapts.
Every 30 seconds. Forever.
"""
import sys, signal, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent_loop import AgentLoop, SpineSensor, SelfInsightSensor
from core.live_probe_sensor import LiveProbeSensor

SPINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spine", "AGENT_SPINE.jsonl")

loop = AgentLoop(
    spine_path=SPINE,
    sensors=[SpineSensor(), SelfInsightSensor(), LiveProbeSensor()]
)

def shutdown(sig, frame):
    print(f"\n[ORGANISM] Signal {sig} - shutting down after {loop.state.cycle} cycles")
    loop.stop()
    import json
    from pathlib import Path
    state_path = Path(SPINE).parent / "ORGANISM_STATE.json"
    with open(state_path, "w") as f:
        json.dump({
            "cycle": loop.state.cycle,
            "beliefs": len(loop.state.beliefs),
            "canonical_ratio": loop.state.canonical_ratio,
            "total_demotions": loop.state.total_demotions,
            "total_actions": loop.state.total_actions_taken,
            "falsification": loop.falsification.summary(),
            "omega": "the loop that changes itself is the first thing worth running"
        }, f, indent=2)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

print(f"[ORGANISM] Spawning. Spine: {SPINE}")
print(f"[ORGANISM] Sensors: SpineSensor, SelfInsightSensor, LiveProbeSensor")
print(f"[ORGANISM] SENSE -> CLASSIFY -> ACT -> RECORD -> FALSIFY -> ADAPT")
print(f"[ORGANISM] Interval: 30s. PID: {os.getpid()}")
loop.run_forever(interval=30.0)
