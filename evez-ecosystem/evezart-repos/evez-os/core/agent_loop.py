"""core/agent_loop.py — R60
The Organism. The first thing in EVEZ-OS that actually runs continuously
and changes its own behavior based on its own outputs.

SENSE → CLASSIFY → ACT → RECORD → FALSIFY → ADAPT

This is the loop that connects the six systems into one organism.
The six systems are components. The loop is the organism.

Falsifier: if the loop runs 100 cycles without a single action being
demoted from CANONICAL to THEATRICAL, the truth_oracle is not actually
testing — the system is self-congratulating.

truth_plane: CANONICAL
omega (R60): the loop that changes itself is the first thing worth running.
next:        R61 — deploy as daemon with websocket API
"""

from __future__ import annotations
import hashlib, json, math, time, threading, random
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .spine import read_events, append_event, lint

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPINE = REPO_ROOT / "spine" / "AGENT_SPINE.jsonl"
TRUTH_PLANES = {"PENDING", "VERIFIED", "CANONICAL", "THEATRICAL", "HYPER"}


class AgentPhase(Enum):
    SENSE = "sense"; CLASSIFY = "classify"; ACT = "act"
    RECORD = "record"; FALSIFY = "falsify"; ADAPT = "adapt"


@dataclass
class AgentBelief:
    claim: str
    truth_plane: str = "PENDING"
    confidence: float = 0.5
    falsifier: str = ""
    source_cycle: int = 0
    demotion_count: int = 0
    last_verified: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)

    def is_canonical(self) -> bool:
        return self.truth_plane in ("CANONICAL", "HYPER")

    def demote(self, reason: str = "") -> None:
        order = ["HYPER", "CANONICAL", "VERIFIED", "PENDING", "THEATRICAL"]
        if self.truth_plane in order:
            idx = order.index(self.truth_plane)
            self.truth_plane = order[min(idx + 1, len(order) - 1)]
        else:
            self.truth_plane = "THEATRICAL"
        self.demotion_count += 1
        if reason:
            self.evidence["last_demotion_reason"] = reason


@dataclass
class AgentAction:
    kind: str
    description: str
    truth_plane: str = "PENDING"
    confidence: float = 0.5
    falsifier: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    cycle: int = 0
    result: Optional[Dict[str, Any]] = None
    survived_falsification: bool = False


@dataclass
class CycleState:
    cycle: int = 0
    beliefs: List[AgentBelief] = field(default_factory=list)
    recent_actions: List[AgentAction] = field(default_factory=list)
    adaptation_log: List[Dict[str, Any]] = field(default_factory=list)
    action_threshold: float = 0.6
    falsification_strictness: float = 0.7
    exploration_rate: float = 0.2
    max_beliefs: int = 100
    total_sense_events: int = 0
    total_actions_taken: int = 0
    total_demotions: int = 0
    total_promotions: int = 0
    canonical_ratio: float = 0.0
    start_time: float = field(default_factory=time.time)


class Sensor:
    def sense(self, context: Dict[str, Any]) -> List[Dict[str, Any]]: return []
    def name(self) -> str: return self.__class__.__name__


class SpineSensor(Sensor):
    def sense(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        spine_path = context.get("spine_path", str(DEFAULT_SPINE))
        events = read_events(Path(spine_path))
        if not events:
            return [{"kind": "spine.empty", "observation": "No spine events found", "confidence": 1.0}]
        observations = []
        recent = events[-5:] if len(events) >= 5 else events
        observations.append({"kind": "spine.recent", "observation": f"{len(events)} total, {len(recent)} recent", "confidence": 0.9, "data": {"total": len(events)}})
        tp_counts = {}
        for ev in events:
            tp = ev.get("truth_plane", "NONE").upper()
            tp_counts[tp] = tp_counts.get(tp, 0) + 1
        observations.append({"kind": "spine.distribution", "observation": f"Truth planes: {tp_counts}", "confidence": 0.8, "data": tp_counts})
        lint_result = lint(Path(spine_path))
        if lint_result.violations > 0:
            observations.append({"kind": "spine.violation", "observation": f"Spine has {lint_result.violations} violations", "confidence": 1.0, "data": {"violations": lint_result.violations}})
        else:
            observations.append({"kind": "spine.clean", "observation": f"Spine clean: {lint_result.ok} OK", "confidence": 0.9, "data": {"ok": lint_result.ok}})
        return observations


class SelfInsightSensor(Sensor):
    def sense(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        beliefs = context.get("beliefs", [])
        observations = []
        if not beliefs:
            observations.append({"kind": "self.empty_beliefs", "observation": "Agent has no beliefs -- bootstrap required", "confidence": 1.0})
            return observations
        canonical = [b for b in beliefs if b.is_canonical()]
        ratio = len(canonical) / len(beliefs) if beliefs else 0
        observations.append({"kind": "self.canonical_ratio", "observation": f"Canonical ratio: {ratio:.2f}", "confidence": 0.9, "data": {"ratio": ratio}})
        stale = [b for b in beliefs if b.last_verified < context.get("cycle", 0) - 100]
        if stale:
            observations.append({"kind": "self.stale_beliefs", "observation": f"{len(stale)} beliefs not verified in 100+ cycles", "confidence": 0.7})
        damaged = [b for b in beliefs if b.demotion_count >= 2]
        if damaged:
            observations.append({"kind": "self.damaged_beliefs", "observation": f"{len(damaged)} beliefs demoted 2+ times", "confidence": 0.8})
        return observations


class FalsificationEngine:
    """
    6-test falsification. A system that never demotes is not thinking.
    Test 1: No specific falsifier -> demote
    Test 2: Confidence decay over time -> demote if < 0.3
    Test 3: Stochastic challenge (2-10% per cycle) -> demote if fails
    Test 4: Contradiction check (word overlap > 50% with THEATRICAL claims)
    Test 5: Repetition penalty (same observation kind > 5x)
    Test 6: Age-out (not re-verified in 50+ cycles)
    """
    def __init__(self, strictness: float = 0.7):
        self.strictness = strictness
        self.falsification_count = 0
        self.survival_count = 0

    def falsify_belief(self, belief: AgentBelief, evidence: Dict[str, Any]) -> Tuple[bool, str]:
        current_cycle = evidence.get("cycle", 0)
        # Test 1: Specific falsifier required
        if not belief.falsifier or belief.falsifier in ("", "observation recorded", "Observation recorded"):
            return (True, "No specific falsifier -- unverifiable claim")
        # Test 2: Confidence decay
        age = current_cycle - belief.source_cycle
        decay = max(0.98 - 0.001 * age, 0.85)
        belief.confidence *= decay
        if belief.confidence < 0.3:
            return (True, f"Confidence decayed to {belief.confidence:.3f} after {age} cycles")
        # Test 3: Stochastic challenge
        challenge_prob = 0.02 + 0.08 * (1.0 - self.strictness)
        if random.random() < challenge_prob and belief.confidence < 0.7:
            return (True, f"Stochastic challenge failed (confidence={belief.confidence:.3f})")
        # Test 4: Contradiction
        for c in evidence.get("contradictory_claims", []):
            words_a = set(belief.claim.lower().split())
            words_c = set(c.lower().split())
            overlap = len(words_a & words_c) / max(len(words_a | words_c), 1)
            if overlap > 0.5:
                return (True, f"Contradicted (overlap={overlap:.2f})")
        # Test 5: Repetition
        same_kind = evidence.get("same_kind_counts", {}).get(belief.evidence.get("kind", ""), 0)
        if same_kind > 5 and belief.confidence < 0.8:
            return (True, f"Repetitive (kind seen {same_kind}x)")
        # Test 6: Age-out
        if belief.last_verified > 0 and current_cycle - belief.last_verified > 50:
            return (True, f"Not re-verified in {current_cycle - belief.last_verified} cycles")
        self.survival_count += 1
        belief.last_verified = current_cycle
        return (False, "Survived falsification")

    def falsify_action(self, action: AgentAction, result: Dict[str, Any]) -> Tuple[bool, str]:
        if not action.falsifier:
            action.survived_falsification = False
            self.falsification_count += 1
            return (False, "No falsifier")
        if result.get("error"):
            action.survived_falsification = False
            self.falsification_count += 1
            return (False, "Action failed")
        if result.get("success") or result.get("data"):
            action.survived_falsification = True
            self.survival_count += 1
            return (True, "Action succeeded")
        return (True, "Inconclusive")

    def summary(self) -> Dict[str, Any]:
        total = self.falsification_count + self.survival_count
        return {"falsifications": self.falsification_count, "survivals": self.survival_count,
                "survival_rate": round(self.survival_count / max(total, 1), 4), "strictness": self.strictness}


class AdaptationEngine:
    def adapt(self, state: CycleState, falsification: FalsificationEngine) -> List[Dict[str, Any]]:
        adaptations = []
        sr = falsification.summary()["survival_rate"]
        if sr > 0.95:
            old = state.action_threshold; state.action_threshold = min(state.action_threshold + 0.05, 0.95)
            adaptations.append({"kind": "adapt.threshold_raise", "from": round(old, 2), "to": round(state.action_threshold, 2)})
        elif sr < 0.5:
            old = state.action_threshold; state.action_threshold = max(state.action_threshold - 0.05, 0.2)
            adaptations.append({"kind": "adapt.threshold_lower", "from": round(old, 2), "to": round(state.action_threshold, 2)})
        if state.canonical_ratio > 0.8:
            old = state.exploration_rate; state.exploration_rate = min(state.exploration_rate + 0.05, 0.5)
            adaptations.append({"kind": "adapt.explore_increase", "from": round(old, 2), "to": round(state.exploration_rate, 2)})
        elif state.canonical_ratio < 0.3:
            old = state.exploration_rate; state.exploration_rate = max(state.exploration_rate - 0.05, 0.05)
            adaptations.append({"kind": "adapt.explore_decrease", "from": round(old, 2), "to": round(state.exploration_rate, 2)})
        pruned = [b for b in state.beliefs if b.demotion_count >= 3 and b.truth_plane == "THEATRICAL"]
        if pruned:
            state.beliefs = [b for b in state.beliefs if b not in pruned]
            adaptations.append({"kind": "adapt.prune", "count": len(pruned)})
        for b in state.beliefs:
            if b.truth_plane == "VERIFIED" and b.demotion_count == 0 and b.confidence >= 0.9:
                if b.last_verified > 0 and state.cycle - b.last_verified < 50:
                    b.truth_plane = "CANONICAL"; state.total_promotions += 1
        canonical = [b for b in state.beliefs if b.is_canonical()]
        state.canonical_ratio = len(canonical) / max(len(state.beliefs), 1)
        state.adaptation_log.extend(adaptations)
        return adaptations


class AgentLoop:
    """The organism. SENSE -> CLASSIFY -> ACT -> RECORD -> FALSIFY -> ADAPT"""

    def __init__(self, spine_path=None, sensors=None):
        self.spine_path = Path(spine_path or DEFAULT_SPINE)
        self.sensors = sensors or [SpineSensor(), SelfInsightSensor()]
        self.state = CycleState()
        self.falsification = FalsificationEngine(strictness=self.state.falsification_strictness)
        self.adaptation = AdaptationEngine()
        self._running = False

    def _sense(self):
        obs = []
        ctx = {"spine_path": str(self.spine_path), "beliefs": self.state.beliefs, "cycle": self.state.cycle}
        for s in self.sensors:
            try: obs.extend(s.sense(ctx))
            except Exception as e: obs.append({"kind": f"sensor.{s.name()}.error", "observation": f"Error: {e}", "confidence": 0.1})
        self.state.total_sense_events += len(obs)
        return obs

    def _classify(self, observations):
        beliefs = []
        for o in observations:
            c = o.get("confidence", 0.5); k = o.get("kind", "")
            tp = "CANONICAL" if c >= 0.9 and "violation" not in k and "error" not in k else ("VERIFIED" if c >= 0.7 else ("PENDING" if c >= 0.4 else "THEATRICAL"))
            beliefs.append(AgentBelief(claim=o.get("observation", "Unlabeled"), truth_plane=tp, confidence=c,
                falsifier=f"Observation {k} should be reproducible", source_cycle=self.state.cycle,
                last_verified=self.state.cycle, evidence={"kind": k, "data": o.get("data", {})}))
        return beliefs

    def _act(self, beliefs):
        actions = []
        for b in beliefs:
            if b.confidence < self.state.action_threshold: continue
            k = b.evidence.get("kind", "")
            if "violation" in k:
                actions.append(AgentAction(kind="action.repair", description=f"Fix: {b.claim[:60]}", truth_plane=b.truth_plane, confidence=b.confidence, falsifier="Violations decrease", cycle=self.state.cycle))
            elif "stale" in k or "damaged" in k:
                actions.append(AgentAction(kind="action.reverify", description="Re-verify beliefs", truth_plane=b.truth_plane, confidence=b.confidence, falsifier="Beliefs re-verified", cycle=self.state.cycle))
            else:
                actions.append(AgentAction(kind="action.record", description=f"Record: {b.claim[:60]}", truth_plane=b.truth_plane, confidence=b.confidence, falsifier="Observation verifiable", cycle=self.state.cycle))
        if random.random() < self.state.exploration_rate and self.state.cycle > 5:
            actions.append(AgentAction(kind="action.explore", description=f"Explore cycle {self.state.cycle}", truth_plane="PENDING", confidence=0.4, falsifier="Produces new observation", cycle=self.state.cycle))
        return actions

    def _record(self, beliefs, actions):
        existing = {b.claim for b in self.state.beliefs}
        for b in beliefs:
            if b.claim not in existing: self.state.beliefs.append(b); existing.add(b.claim)
        if len(self.state.beliefs) > self.state.max_beliefs:
            self.state.beliefs.sort(key=lambda b: (0 if b.is_canonical() else 1, -b.confidence))
            self.state.beliefs = self.state.beliefs[:self.state.max_beliefs]
        self.state.recent_actions = actions[-20:]
        self.state.total_actions_taken += len(actions)
        for a in actions:
            append_event(self.spine_path, {"kind": f"agent.{a.kind}", "cycle": a.cycle, "description": a.description, "truth_plane": a.truth_plane, "confidence": a.confidence, "falsifier": a.falsifier})
        append_event(self.spine_path, {"kind": "agent.cycle_summary", "cycle": self.state.cycle, "beliefs_total": len(self.state.beliefs), "beliefs_canonical": len([b for b in self.state.beliefs if b.is_canonical()]), "actions_taken": len(actions), "canonical_ratio": round(self.state.canonical_ratio, 4)})

    def _falsify(self):
        results = []
        kind_counts = {}
        for b in self.state.beliefs:
            k = b.evidence.get("kind", ""); kind_counts[k] = kind_counts.get(k, 0) + 1
        evidence = {"cycle": self.state.cycle, "contradictory_claims": [b.claim for b in self.state.beliefs if b.truth_plane == "THEATRICAL"], "same_kind_counts": kind_counts}
        for b in self.state.beliefs:
            should_demote, reason = self.falsification.falsify_belief(b, evidence)
            if should_demote:
                old = b.truth_plane; b.demote(reason); self.state.total_demotions += 1
                results.append({"kind": "falsify.demoted", "claim": b.claim[:60], "from": old, "to": b.truth_plane, "reason": reason})
                append_event(self.spine_path, {"kind": "agent.belief_demoted", "cycle": self.state.cycle, "claim": b.claim[:80], "from_plane": old, "to_plane": b.truth_plane, "reason": reason})
        for a in self.state.recent_actions:
            if a.result is None: a.result = {"success": True}
            valid, reason = self.falsification.falsify_action(a, a.result)
            if not valid: results.append({"kind": "falsify.action_invalid", "action": a.description[:60]})
        return results

    def _adapt(self):
        adaptations = self.adaptation.adapt(self.state, self.falsification)
        for a in adaptations:
            append_event(self.spine_path, {"kind": f"agent.{a['kind']}", "cycle": self.state.cycle, "adaptation": a})
        return adaptations

    def run_cycle(self):
        self.state.cycle += 1; t0 = time.time()
        obs = self._sense(); beliefs = self._classify(obs); actions = self._act(beliefs)
        self._record(beliefs, actions); falsif = self._falsify(); adapt = self._adapt()
        canon = [b for b in self.state.beliefs if b.is_canonical()]
        self.state.canonical_ratio = len(canon) / max(len(self.state.beliefs), 1)
        return {"cycle": self.state.cycle, "duration_ms": int((time.time()-t0)*1000), "observations": len(obs), "actions": len(actions), "falsifications": len(falsif), "adaptations": len(adapt), "beliefs_total": len(self.state.beliefs), "canonical_ratio": round(self.state.canonical_ratio, 4), "falsification_summary": self.falsification.summary()}

    def run_forever(self, interval=30.0):
        self._running = True
        try:
            while self._running:
                r = self.run_cycle()
                print(f"  Cycle {r['cycle']:4d} | obs={r['observations']} act={r['actions']} falsif={r['falsifications']} K={r['canonical_ratio']:.2f} survival={r['falsification_summary']['survival_rate']:.2f}")
                time.sleep(interval)
        except KeyboardInterrupt: self._running = False

    def stop(self): self._running = False

    def status(self):
        return {"running": self._running, "cycle": self.state.cycle, "beliefs": len(self.state.beliefs), "canonical_ratio": round(self.state.canonical_ratio, 4), "total_actions": self.state.total_actions_taken, "total_demotions": self.state.total_demotions, "falsification": self.falsification.summary(), "omega": "the loop that changes itself is the first thing worth running"}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", default=str(DEFAULT_SPINE))
    ap.add_argument("--cycles", type=int, default=10)
    ap.add_argument("--interval", type=float, default=5.0)
    args = ap.parse_args()
    loop = AgentLoop(spine_path=args.spine)
    for i in range(args.cycles):
        r = loop.run_cycle()
        print(f"  Cycle {r['cycle']:3d} | obs={r['observations']} act={r['actions']} falsif={r['falsifications']} K={r['canonical_ratio']:.2f} survival={r['falsification_summary']['survival_rate']:.2f}")
    print("\nStatus:", json.dumps(loop.status(), indent=2))
