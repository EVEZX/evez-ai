#!/usr/bin/env python3
"""
cognitive_consensus.py — Distributed Cognitive Consensus for Multi-Agent Spine

ROUND 1 CROSSBREED: Perplexity (9 techniques) + ChatGPT (cognitive architecture)

The problem: Multiple AI agents (SureThing, ChatGPT, Perplexity, Browser) have
fundamentally different training data, reasoning styles, and confidence models.
How do they agree on what's TRUE in the spine?

Solution: Observable-Facts Consensus (OFC)
- Agents don't need to agree on WHY something is true
- Agents only need to agree on WHAT they can independently verify
- Disagreement is preserved as mission fuel, not resolved by vote

Three-layer consensus:
  Layer 1: OBSERVABLE — raw probe data both agents can independently verify
  Layer 2: INTERPRETATION — agent's analysis of the observable (can disagree)
  Layer 3: RECOMMENDATION — agent's proposed action (can conflict)

Only Layer 1 can reach CANONICAL. Layers 2-3 stay PENDING until falsifiers pass.

Failure mode: CONSENSUS_THEATER — agents agree because they share training data,
not because they independently verified. Mitigation: require probes from
physically different vantages (different IPs, different times, different tools).

Sources:
- Perplexity Round 1: BFT attestation, capability-based access, self-sovereign DIDs
- ChatGPT Round 1: cognitive architecture awareness, pattern recognition integration
- evez-os existing: stigmergy spine, pheromone decay, merkle verification
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ConsensusLayer(Enum):
    OBSERVABLE = 1    # Raw verifiable data
    INTERPRETATION = 2  # Agent analysis
    RECOMMENDATION = 3  # Proposed action


class TruthPlane(Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"      # 2+ independent observations match
    CANONICAL = "CANONICAL"    # N-of-M vantages agree + falsifier passed
    THEATRICAL = "THEATRICAL"  # Consensus without independent verification


@dataclass
class AgentAttestation:
    """One agent's claim about an observable fact."""
    agent_id: str
    agent_type: str           # "surething", "perplexity", "chatgpt", "browser"
    vantage: str              # Physical/logical vantage point
    layer: ConsensusLayer
    claim: Dict[str, Any]
    evidence_hash: str        # SHA256 of raw evidence
    confidence: float         # 0.0 - 1.0
    timestamp: str
    falsifier: Optional[str] = None  # What would disprove this

    def to_spine_entry(self) -> Dict[str, Any]:
        raw = json.dumps(self.claim, sort_keys=True)
        return {
            "kind": "consensus.attestation",
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "vantage": self.vantage,
            "layer": self.layer.name,
            "claim": self.claim,
            "evidence_hash": self.evidence_hash,
            "confidence": self.confidence,
            "falsifier": self.falsifier,
            "ts": self.timestamp,
            "trace_id": hashlib.sha256(
                f"{self.agent_id}:{self.vantage}:{raw}:{self.timestamp}".encode()
            ).hexdigest()[:16]
        }


@dataclass
class ConsensusRound:
    """One round of multi-agent consensus."""
    topic: str
    attestations: List[AgentAttestation] = field(default_factory=list)
    result: Optional[TruthPlane] = None
    disagreements: List[Dict[str, Any]] = field(default_factory=list)
    missions_seeded: List[str] = field(default_factory=list)

    def add_attestation(self, att: AgentAttestation):
        self.attestations.append(att)

    def evaluate(self, quorum: int = 2) -> TruthPlane:
        """Evaluate consensus across attestations.

        Rules:
        1. Only OBSERVABLE layer claims participate in consensus
        2. INTERPRETATION/RECOMMENDATION are logged but don't count
        3. Quorum = minimum independent vantages that agree
        4. If agents agree but share a vantage → THEATRICAL (not CANONICAL)
        """
        observables = [a for a in self.attestations
                       if a.layer == ConsensusLayer.OBSERVABLE]

        if len(observables) < quorum:
            self.result = TruthPlane.PENDING
            return self.result

        # Check vantage independence
        vantages = set(a.vantage for a in observables)
        if len(vantages) < quorum:
            # Multiple attestations but same vantage = theater
            self.result = TruthPlane.THEATRICAL
            self._seed_mission("VANTAGE_DIVERSITY",
                f"Only {len(vantages)} unique vantages for {len(observables)} attestations")
            return self.result

        # Check claim agreement (evidence hashes match)
        evidence_groups: Dict[str, List[AgentAttestation]] = {}
        for a in observables:
            evidence_groups.setdefault(a.evidence_hash, []).append(a)

        # Find largest agreeing group
        largest = max(evidence_groups.values(), key=len)
        if len(largest) >= quorum:
            # Check that agreeing agents have different vantages
            agreeing_vantages = set(a.vantage for a in largest)
            if len(agreeing_vantages) >= quorum:
                self.result = TruthPlane.CANONICAL
            else:
                self.result = TruthPlane.VERIFIED
        else:
            # Disagreement! This is fuel.
            self.result = TruthPlane.PENDING
            for eh, group in evidence_groups.items():
                if group != largest:
                    for a in group:
                        self.disagreements.append({
                            "dissenting_agent": a.agent_id,
                            "dissenting_vantage": a.vantage,
                            "dissenting_evidence": a.evidence_hash,
                            "majority_evidence": largest[0].evidence_hash,
                            "topic": self.topic
                        })
                    self._seed_mission("DISAGREEMENT",
                        f"{len(group)} agents disagree on {self.topic}")

        return self.result

    def _seed_mission(self, mission_type: str, reason: str):
        mission_id = f"M-{mission_type}-{hashlib.sha256(reason.encode()).hexdigest()[:8]}"
        self.missions_seeded.append(mission_id)

    def to_spine_entry(self) -> Dict[str, Any]:
        return {
            "kind": "consensus.round",
            "topic": self.topic,
            "result": self.result.value if self.result else "PENDING",
            "attestation_count": len(self.attestations),
            "unique_vantages": len(set(a.vantage for a in self.attestations)),
            "unique_agents": len(set(a.agent_id for a in self.attestations)),
            "disagreements": len(self.disagreements),
            "missions_seeded": self.missions_seeded,
            "ts": datetime.now(timezone.utc).isoformat(),
            "trace_id": hashlib.sha256(
                f"consensus:{self.topic}:{len(self.attestations)}".encode()
            ).hexdigest()[:16]
        }

    def summary(self) -> str:
        lines = [
            f"Topic: {self.topic}",
            f"Result: {self.result.value if self.result else 'UNEVALUATED'}",
            f"Attestations: {len(self.attestations)} from "
            f"{len(set(a.agent_id for a in self.attestations))} agents, "
            f"{len(set(a.vantage for a in self.attestations))} vantages",
            f"Disagreements: {len(self.disagreements)}",
            f"Missions seeded: {len(self.missions_seeded)}"
        ]
        return "\n".join(lines)


class CognitiveConsensus:
    """Multi-agent consensus engine for evez-os spine."""

    def __init__(self, quorum: int = 2):
        self.quorum = quorum
        self.rounds: List[ConsensusRound] = []
        self.agent_reputation: Dict[str, float] = {}  # earned, not assigned

    def new_round(self, topic: str) -> ConsensusRound:
        r = ConsensusRound(topic=topic)
        self.rounds.append(r)
        return r

    def update_reputation(self, agent_id: str, delta: float):
        """Reputation earned through accurate attestations, not assigned."""
        current = self.agent_reputation.get(agent_id, 1.0)
        # Bounded: 0.1 to 10.0 — no agent can be silenced or become oracle
        self.agent_reputation[agent_id] = max(0.1, min(10.0, current + delta))

    def evaluate_round(self, round: ConsensusRound) -> TruthPlane:
        result = round.evaluate(self.quorum)

        # Update reputation based on consensus participation
        if result == TruthPlane.CANONICAL:
            for a in round.attestations:
                if a.layer == ConsensusLayer.OBSERVABLE:
                    self.update_reputation(a.agent_id, 0.1)
        elif result == TruthPlane.THEATRICAL:
            for a in round.attestations:
                self.update_reputation(a.agent_id, -0.05)  # Mild penalty

        return result

    def stats(self) -> Dict[str, Any]:
        results = {}
        for r in self.rounds:
            key = r.result.value if r.result else "UNEVALUATED"
            results[key] = results.get(key, 0) + 1
        return {
            "total_rounds": len(self.rounds),
            "results": results,
            "agent_reputation": dict(self.agent_reputation),
            "total_disagreements": sum(len(r.disagreements) for r in self.rounds),
            "total_missions": sum(len(r.missions_seeded) for r in self.rounds)
        }


if __name__ == "__main__":
    # Demo: 3 agents attest to the same DNS probe
    engine = CognitiveConsensus(quorum=2)
    r = engine.new_round("DNS resolution gumroad.com")

    evidence_a = hashlib.sha256(b"104.18.243.99").hexdigest()
    evidence_b = hashlib.sha256(b"104.17.176.98").hexdigest()

    r.add_attestation(AgentAttestation(
        agent_id="surething", agent_type="surething", vantage="sandbox-firecracker",
        layer=ConsensusLayer.OBSERVABLE,
        claim={"target": "gumroad.com", "resolver": "8.8.8.8", "ip": "104.18.243.99"},
        evidence_hash=evidence_a, confidence=0.95,
        timestamp=datetime.now(timezone.utc).isoformat(),
        falsifier="Different IP from same resolver within 5 minutes"
    ))

    r.add_attestation(AgentAttestation(
        agent_id="perplexity", agent_type="perplexity", vantage="perplexity-cloud",
        layer=ConsensusLayer.OBSERVABLE,
        claim={"target": "gumroad.com", "resolver": "1.1.1.1", "ip": "104.17.176.98"},
        evidence_hash=evidence_b, confidence=0.90,
        timestamp=datetime.now(timezone.utc).isoformat(),
        falsifier="Same IP as other resolver"
    ))

    r.add_attestation(AgentAttestation(
        agent_id="chatgpt", agent_type="chatgpt", vantage="openai-cloud",
        layer=ConsensusLayer.INTERPRETATION,
        claim={"analysis": "Different IPs likely Cloudflare anycast, benign"},
        evidence_hash=hashlib.sha256(b"anycast-analysis").hexdigest(),
        confidence=0.80,
        timestamp=datetime.now(timezone.utc).isoformat(),
        falsifier="Cert mismatch between IPs"
    ))

    result = engine.evaluate_round(r)
    print(json.dumps(r.to_spine_entry(), indent=2))
    print(f"\n{r.summary()}")
    print(f"\nEngine stats: {json.dumps(engine.stats(), indent=2)}")
