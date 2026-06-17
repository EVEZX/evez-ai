"""Failure-Surface Cartography (FSC) - Cycle Logging System.

Implements comprehensive failure analysis and surface mapping:
- Failure motif detection and classification
- Surface topology mapping (DNS, BGP, TLS, CDN, AUTH, ROLLBACK)
- Cycle logging with append-only event spines
- Forensic episode generation
- Predictive failure surface analysis
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from .spine import append_event, read_events
from .quantum_rng import random_float


class FailureDomain(Enum):
    """Domains where failures can occur."""
    DNS = auto()
    BGP = auto()
    TLS = auto()
    CDN = auto()
    AUTH = auto()
    ROLLBACK = auto()
    PROCESS = auto()
    MEMORY = auto()
    NETWORK = auto()
    UNKNOWN = auto()


class FailureSeverity(Enum):
    """Severity levels for failures."""
    TRANSIENT = auto()      # Self-healing
    RECOVERABLE = auto()    # Can be recovered
    DEGRADED = auto()       # Reduced functionality
    CRITICAL = auto()       # System failure
    CATASTROPHIC = auto()   # Data loss/corruption


@dataclass
class FailureMotif:
    """A recurring failure pattern."""
    motif_id: str
    domain: FailureDomain
    signature: str
    trigger_pattern: str
    manifestation: str
    frequency: float
    first_seen: float
    last_seen: float
    occurrences: int = 0
    contexts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "motif_id": self.motif_id,
            "domain": self.domain.name,
            "signature": self.signature,
            "trigger_pattern": self.trigger_pattern,
            "manifestation": self.manifestation,
            "frequency": self.frequency,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "occurrences": self.occurrences
        }


@dataclass
class FailureEvent:
    """A single failure event."""
    event_id: str
    domain: FailureDomain
    severity: FailureSeverity
    description: str
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    related_events: List[str] = field(default_factory=list)
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = hashlib.sha256(
                f"{self.domain.name}:{self.timestamp}:{self.description}".encode()
            ).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "domain": self.domain.name,
            "severity": self.severity.name,
            "description": self.description,
            "timestamp": self.timestamp,
            "context": self.context,
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful
        }


@dataclass
class SurfaceTopology:
    """Topology of a failure surface."""
    domain: FailureDomain
    nodes: Set[str] = field(default_factory=set)
    edges: List[Tuple[str, str, float]] = field(default_factory=list)  # (from, to, weight)
    critical_paths: List[List[str]] = field(default_factory=list)
    vulnerability_score: float = 0.0
    last_updated: float = field(default_factory=time.time)


class FailureSurfaceCartographer:
    """Map and analyze failure surfaces."""
    
    def __init__(self, spine_path: Optional[Path] = None):
        self.spine_path = spine_path or Path("fsc_spine.jsonl")
        self.events: List[FailureEvent] = []
        self.motifs: Dict[str, FailureMotif] = {}
        self.topologies: Dict[FailureDomain, SurfaceTopology] = {}
        self.domain_stats: Dict[FailureDomain, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "severities": defaultdict(int),
            "recovery_rate": 0.0
        })
    
    def log_failure(self, domain: FailureDomain, severity: FailureSeverity,
                    description: str, context: Dict[str, Any] = None,
                    stack_trace: str = None) -> FailureEvent:
        """Log a failure event."""
        event = FailureEvent(
            event_id="",
            domain=domain,
            severity=severity,
            description=description,
            timestamp=time.time(),
            context=context or {},
            stack_trace=stack_trace
        )
        
        # Add to memory
        self.events.append(event)
        
        # Update stats
        self.domain_stats[domain]["count"] += 1
        self.domain_stats[domain]["severities"][severity.name] += 1
        
        # Log to spine
        self._append_to_spine(event)
        
        # Update topology
        self._update_topology(event)
        
        # Check for motifs
        self._detect_motifs(event)
        
        return event
    
    def _append_to_spine(self, event: FailureEvent) -> None:
        """Append event to spine."""
        spine_event = {
            "type": "failure",
            **event.to_dict()
        }
        append_event(self.spine_path, spine_event)
    
    def _update_topology(self, event: FailureEvent) -> None:
        """Update surface topology based on event."""
        domain = event.domain
        
        if domain not in self.topologies:
            self.topologies[domain] = SurfaceTopology(domain=domain)
        
        topo = self.topologies[domain]
        
        # Extract nodes from context
        nodes = set()
        for key, value in event.context.items():
            if isinstance(value, str):
                nodes.add(f"{key}:{value}")
            elif isinstance(value, (list, tuple)):
                for v in value:
                    nodes.add(f"{key}:{v}")
        
        topo.nodes.update(nodes)
        
        # Add edges between related nodes
        nodes_list = list(nodes)
        for i, n1 in enumerate(nodes_list):
            for n2 in nodes_list[i+1:]:
                # Check if edge exists
                existing = [e for e in topo.edges if (e[0] == n1 and e[1] == n2) or (e[0] == n2 and e[1] == n1)]
                
                if existing:
                    # Strengthen edge
                    idx = topo.edges.index(existing[0])
                    topo.edges[idx] = (n1, n2, min(1.0, existing[0][2] + 0.1))
                else:
                    topo.edges.append((n1, n2, 0.1))
        
        # Update vulnerability score
        severity_weights = {
            FailureSeverity.TRANSIENT: 0.1,
            FailureSeverity.RECOVERABLE: 0.3,
            FailureSeverity.DEGRADED: 0.5,
            FailureSeverity.CRITICAL: 0.8,
            FailureSeverity.CATASTROPHIC: 1.0
        }
        
        topo.vulnerability_score = min(1.0, topo.vulnerability_score + severity_weights.get(event.severity, 0.1) * 0.1)
        topo.last_updated = time.time()
    
    def _detect_motifs(self, new_event: FailureEvent) -> None:
        """Detect recurring failure motifs."""
        # Look for similar recent events
        recent_events = [
            e for e in self.events
            if e.domain == new_event.domain
            and e.timestamp > time.time() - 3600  # Last hour
            and e.event_id != new_event.event_id
        ]
        
        # Group by similar description
        similar = [
            e for e in recent_events
            if self._similarity(e.description, new_event.description) > 0.7
        ]
        
        if len(similar) >= 2:
            # Create or update motif
            sig = self._generate_signature(new_event.description)
            
            if sig in self.motifs:
                motif = self.motifs[sig]
                motif.occurrences += 1
                motif.last_seen = time.time()
                motif.frequency = motif.occurrences / (motif.last_seen - motif.first_seen + 1)
            else:
                motif = FailureMotif(
                    motif_id=hashlib.sha256(sig.encode()).hexdigest()[:12],
                    domain=new_event.domain,
                    signature=sig,
                    trigger_pattern=self._extract_trigger(new_event),
                    manifestation=new_event.description[:100],
                    frequency=1.0,
                    first_seen=time.time(),
                    last_seen=time.time()
                )
                self.motifs[sig] = motif
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate string similarity."""
        # Simple Jaccard similarity on words
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = len(words_a & words_b)
        union = len(words_a | words_b)
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_signature(self, description: str) -> str:
        """Generate signature for failure description."""
        # Normalize and hash
        normalized = description.lower().strip()
        # Remove variable parts (numbers, IDs)
        import re
        normalized = re.sub(r'\d+', 'N', normalized)
        normalized = re.sub(r'[a-f0-9]{8,}', 'HASH', normalized)
        
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def _extract_trigger(self, event: FailureEvent) -> str:
        """Extract trigger pattern from event context."""
        triggers = []
        
        for key, value in event.context.items():
            if key in ("trigger", "cause", "input", "request"):
                triggers.append(f"{key}={value}")
        
        return ";".join(triggers) if triggers else "unknown"
    
    def get_surface_report(self, domain: FailureDomain = None) -> Dict[str, Any]:
        """Get comprehensive surface report."""
        if domain:
            topo = self.topologies.get(domain)
            if not topo:
                return {"error": f"No data for domain {domain.name}"}
            
            return {
                "domain": domain.name,
                "nodes": len(topo.nodes),
                "edges": len(topo.edges),
                "vulnerability_score": topo.vulnerability_score,
                "critical_paths": len(topo.critical_paths),
                "event_count": self.domain_stats[domain]["count"],
                "severities": dict(self.domain_stats[domain]["severities"])
            }
        
        # All domains
        return {
            "domains": {
                d.name: self.get_surface_report(d)
                for d in self.topologies.keys()
            },
            "total_events": len(self.events),
            "total_motifs": len(self.motifs),
            "most_vulnerable": max(
                self.topologies.items(),
                key=lambda x: x[1].vulnerability_score
            )[0].name if self.topologies else None
        }
    
    def predict_failure(self, domain: FailureDomain, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict likelihood of failure in given context."""
        # Check for matching motifs
        matching_motifs = [
            m for m in self.motifs.values()
            if m.domain == domain
        ]
        
        # Calculate base probability from vulnerability score
        topo = self.topologies.get(domain)
        base_prob = topo.vulnerability_score if topo else 0.1
        
        # Adjust based on motifs
        motif_boost = len(matching_motifs) * 0.05
        
        # Adjust based on recent failures
        recent_failures = len([
            e for e in self.events
            if e.domain == domain
            and e.timestamp > time.time() - 300  # 5 minutes
        ])
        recent_boost = min(0.3, recent_failures * 0.05)
        
        probability = min(0.95, base_prob + motif_boost + recent_boost)
        
        return {
            "domain": domain.name,
            "failure_probability": probability,
            "matching_motifs": len(matching_motifs),
            "recent_failures": recent_failures,
            "risk_level": "HIGH" if probability > 0.7 else "MEDIUM" if probability > 0.3 else "LOW"
        }
    
    def get_recovery_recommendations(self, event: FailureEvent) -> List[str]:
        """Get recovery recommendations for a failure."""
        recommendations = []
        
        if event.domain == FailureDomain.DNS:
            recommendations.extend([
                "Check DNS resolver configuration",
                "Verify zone file integrity",
                "Test alternative DNS servers"
            ])
        elif event.domain == FailureDomain.BGP:
            recommendations.extend([
                "Verify route announcements",
                "Check peering sessions",
                "Review prefix filters"
            ])
        elif event.domain == FailureDomain.TLS:
            recommendations.extend([
                "Verify certificate validity",
                "Check cipher suite compatibility",
                "Review TLS configuration"
            ])
        elif event.domain == FailureDomain.ROLLBACK:
            recommendations.extend([
                "Verify snapshot integrity",
                "Check rewind window bounds",
                "Validate state checksums"
            ])
        
        # Add generic recommendations based on severity
        if event.severity in (FailureSeverity.CRITICAL, FailureSeverity.CATASTROPHIC):
            recommendations.insert(0, "INITIATE EMERGENCY PROTOCOL")
            recommendations.insert(1, "NOTIFY ON-CALL ENGINEER")
        
        return recommendations


class CycleLogger:
    """Log failure cycles with append-only spine."""
    
    def __init__(self, spine_path: Path):
        self.spine_path = spine_path
        self.cycle_count = 0
    
    def start_cycle(self, cycle_type: str, context: Dict[str, Any] = None) -> str:
        """Start a new cycle."""
        self.cycle_count += 1
        cycle_id = f"cycle_{self.cycle_count}_{int(time.time())}"
        
        event = {
            "type": "cycle_start",
            "cycle_id": cycle_id,
            "cycle_type": cycle_type,
            "context": context or {},
            "timestamp": time.time()
        }
        
        append_event(self.spine_path, event)
        return cycle_id
    
    def log_phase(self, cycle_id: str, phase: str, data: Dict[str, Any]) -> None:
        """Log a phase within a cycle."""
        event = {
            "type": "cycle_phase",
            "cycle_id": cycle_id,
            "phase": phase,
            "data": data,
            "timestamp": time.time()
        }
        
        append_event(self.spine_path, event)
    
    def end_cycle(self, cycle_id: str, outcome: str, metrics: Dict[str, Any]) -> None:
        """End a cycle."""
        event = {
            "type": "cycle_end",
            "cycle_id": cycle_id,
            "outcome": outcome,
            "metrics": metrics,
            "timestamp": time.time()
        }
        
        append_event(self.spine_path, event)


# Convenience functions
_cartographer: Optional[FailureSurfaceCartographer] = None


def initialize(spine_path: Optional[Path] = None) -> FailureSurfaceCartographer:
    """Initialize global cartographer."""
    global _cartographer
    _cartographer = FailureSurfaceCartographer(spine_path)
    return _cartographer


def get_cartographer() -> FailureSurfaceCartographer:
    """Get global cartographer."""
    if _cartographer is None:
        return initialize()
    return _cartographer


def log(domain: FailureDomain, severity: FailureSeverity, description: str, **kwargs) -> FailureEvent:
    """Log a failure event."""
    return get_cartographer().log_failure(domain, severity, description, kwargs)
