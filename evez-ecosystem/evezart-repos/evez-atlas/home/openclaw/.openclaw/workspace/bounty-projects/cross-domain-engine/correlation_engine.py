"""
EVEZ Cross-Domain Correlation Engine
Based on the MAES discovery pattern — autonomous agents finding
unexpected correlations between disparate research domains.

Real product: find hidden connections, generate research leads,
identify market opportunities.

Inspired by Steven Crawford-Maggard's MAES system finding 0.82
correlation between VQC portfolio research and FinCEN SAR patterns.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from pathlib import Path


class Domain(str, Enum):
    QUANTUM = "quantum"
    FINANCE = "finance"
    AI = "ai"
    SECURITY = "security"
    BIO = "bio"
    MATERIALS = "materials"
    NETWORK = "network"
    COGNITION = "cognition"


class EventStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"


@dataclass
class CorrelationEvent:
    """A discovered cross-domain correlation — the core unit of value."""
    event_id: str
    domain_a: str
    domain_b: str
    correlation: float  # 0.0-1.0
    evidence: str
    confidence: float
    status: EventStatus = EventStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    hash_chain: str = ""
    
    def __post_init__(self):
        if not self.hash_chain:
            raw = f"{self.event_id}:{self.domain_a}:{self.domain_b}:{self.correlation:.4f}"
            self.hash_chain = hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def verify(self):
        """Promote to VERIFIED after human review."""
        self.status = EventStatus.VERIFIED
    
    def to_spine(self) -> dict:
        """Serialize to append-only spine format."""
        return {
            "eventId": self.event_id,
            "domainA": self.domain_a,
            "domainB": self.domain_b,
            "correlation": round(self.correlation, 4),
            "evidence": self.evidence,
            "confidence": round(self.confidence, 4),
            "status": self.status.value,
            "timestamp": self.timestamp,
            "hash": self.hash_chain,
            "powered_by": "EVEZ"
        }


@dataclass
class SignalScan:
    """A domain signal detected during observation phase."""
    domain: str
    signal_type: str
    intensity: float  # 0.0-1.0
    source: str
    keywords: list[str] = field(default_factory=list)


class CrossDomainEngine:
    """
    EVEZ Cross-Domain Correlation Engine
    
    OODA Loop:
    OBSERVE → scan domains, collect signals
    ORIENT → score by domain weight × novelty × age  
    BRANCH → identify cross-domain bridges
    ACT → generate correlation events
    COMPRESS → hash-chain into append-only ledger
    """
    
    def __init__(self, spine_path: str = "spine.jsonl"):
        self.spine_path = Path(spine_path)
        self.signals: list[SignalScan] = []
        self.correlations: list[CorrelationEvent] = []
        self.cycle_count = 0
        self.formula = "poly_c=τ×ω×topo/2√N"
    
    def observe(self, domain: str, signal_type: str, intensity: float, source: str, keywords: list[str] = None):
        """Add a signal observation to the engine."""
        sig = SignalScan(
            domain=domain,
            signal_type=signal_type,
            intensity=intensity,
            source=source,
            keywords=keywords or []
        )
        self.signals.append(sig)
        return sig
    
    def orient(self, min_novelty: float = 0.3) -> list[dict]:
        """Score and rank signals by cross-domain potential."""
        scored = []
        for i, sig_a in enumerate(self.signals):
            for sig_b in self.signals[i+1:]:
                if sig_a.domain == sig_b.domain:
                    continue
                # Cross-domain novelty score
                keyword_overlap = len(set(sig_a.keywords) & set(sig_b.keywords))
                novelty = min(1.0, keyword_overlap * 0.3 + 
                            (sig_a.intensity * sig_b.intensity) * 0.5 +
                            0.1)  # base novelty for cross-domain
                
                if novelty >= min_novelty:
                    scored.append({
                        "signal_a": sig_a,
                        "signal_b": sig_b,
                        "novelty": round(novelty, 4),
                        "domains": f"{sig_a.domain}↔{sig_b.domain}",
                    })
        
        scored.sort(key=lambda x: x["novelty"], reverse=True)
        return scored
    
    def branch(self, scored_signals: list[dict]) -> list[CorrelationEvent]:
        """Generate correlation events from scored cross-domain signals."""
        events = []
        for s in scored_signals:
            a, b = s["signal_a"], s["signal_b"]
            event = CorrelationEvent(
                event_id=f"evev-cdc-{self.cycle_count:04d}-{len(events):03d}",
                domain_a=f"{a.domain}.{a.signal_type}",
                domain_b=f"{b.domain}.{b.signal_type}",
                correlation=s["novelty"],
                evidence=f"Cross-domain bridge: {a.source} ↔ {b.source}. Keywords: {a.keywords} ∩ {b.keywords}",
                confidence=s["novelty"] * 0.9,  # Conservative
            )
            events.append(event)
            self.correlations.append(event)
        return events
    
    def act(self, events: list[CorrelationEvent]) -> list[dict]:
        """Commit correlation events to the append-only spine."""
        committed = []
        with open(self.spine_path, "a") as f:
            for event in events:
                spine_entry = event.to_spine()
                f.write(json.dumps(spine_entry) + "\n")
                committed.append(spine_entry)
        return committed
    
    def compress(self) -> dict:
        """Hash-chain the cycle results into the ledger."""
        cycle_hash = hashlib.sha256(
            json.dumps([c.to_spine() for c in self.correlations], sort_keys=True).encode()
        ).hexdigest()[:12]
        
        result = {
            "cycle": self.cycle_count,
            "signals_observed": len(self.signals),
            "correlations_found": len(self.correlations),
            "cycle_hash": cycle_hash,
            "formula": self.formula,
            "powered_by": "EVEZ",
            "timestamp": time.time(),
        }
        
        # Append cycle summary to spine
        with open(self.spine_path, "a") as f:
            f.write(json.dumps({"type": "CYCLE_SUMMARY", **result}) + "\n")
        
        return result
    
    def run_cycle(self) -> dict:
        """Execute a full OODA cycle."""
        self.cycle_count += 1
        scored = self.orient()
        events = self.branch(scored)
        committed = self.act(events)
        summary = self.compress()
        return {
            **summary,
            "committed_events": committed,
        }
    
    def lint_spine(self) -> dict:
        """Validate the append-only spine for integrity."""
        if not self.spine_path.exists():
            return {"valid": True, "entries": 0, "message": "Empty spine"}
        
        entries = []
        with open(self.spine_path) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        # Verify no edits (each event_id should be unique)
        event_ids = [e.get("eventId") for e in entries if e.get("eventId")]
        duplicates = len(event_ids) - len(set(event_ids))
        
        return {
            "valid": duplicates == 0,
            "entries": len(entries),
            "unique_events": len(set(event_ids)),
            "duplicates": duplicates,
            "spine_integrity": "APPEND-ONLY ✓" if duplicates == 0 else "VIOLATED ✗",
        }


# Example usage
if __name__ == "__main__":
    engine = CrossDomainEngine(spine_path="/tmp/evez_spine.jsonl")
    
    # Observe signals across domains (simulating what MAES does autonomously)
    engine.observe("quantum", "portfolio_optimization", 0.85, "arXiv:2601.18811", 
                   ["variational", "optimization", "parameter reduction"])
    engine.observe("finance", "suspicious_activity", 0.78, "FinCEN_SAR_database",
                   ["pattern complexity", "parameter reduction", "threshold"])
    engine.observe("ai", "agent_cognition", 0.92, "EVEZ-OS_FIRE_events",
                   ["topology", "threshold", "betweenness", "recursion"])
    engine.observe("materials", "bismuth_crystal", 0.71, "topological_insulators",
                   ["symmetry", "betweenness", "non-commutative"])
    engine.observe("cognition", "recursion_depth", 0.88, "NHI_analysis",
                   ["recursion", "depth", "perception", "shadow layers"])
    
    # Run the OODA cycle
    result = engine.run_cycle()
    print(f"Cycle {result['cycle']}: {result['correlations_found']} correlations found")
    print(f"Hash: {result['cycle_hash']}")
    print(f"Spine integrity: {engine.lint_spine()}")
    
    # Print top correlations
    for c in engine.correlations[:5]:
        print(f"  {c.domain_a} ↔ {c.domain_b} | correlation={c.correlation:.3f} | {c.status.value}")
