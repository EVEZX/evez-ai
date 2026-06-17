"""
Test Harness + Deterministic Replay Tooling
Replays any spine segment and verifies FSC + cognition invariants.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from .spine import AppendOnlySpine
from .fsc import FSC
from .cognition_wheel import CognitionWheel


class ReplayTestHarness:
    def __init__(self, spine_path: Path):
        self.spine_path = spine_path
        self.fsc = FSC()
        self.wheel = CognitionWheel()

    def replay(self, from_hash: str = None, to_hash: str = None) -> Dict[str, Any]:
        spine = AppendOnlySpine(self.spine_path)
        results = []

        for event in spine._events:
            if from_hash and event.hash < from_hash:
                continue
            if to_hash and event.hash > to_hash:
                break

            anomaly = event.payload.get("anomaly", "none")
            cycle = self.fsc.cycle(anomaly, ["R4", "R5"])
            results.append({
                "event_hash": event.hash,
                "anomaly": anomaly,
                "Ω": cycle.Ω,
                "tests_passed": cycle.tests_passed,
                "accepted": cycle.Ω < 0.2 and cycle.tests_passed == cycle.tests_run
            })

        return {
            "replayed_events": len(results),
            "results": results,
            "all_passed": all(r["accepted"] for r in results)
        }

    def run_full_suite(self) -> Dict[str, Any]:
        return self.replay()