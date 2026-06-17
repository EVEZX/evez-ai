"""Play Forever Engine - Infinite Forensic Episode Generation.

Generates infinite forensic episodes from failure motifs across:
- DNS lobbies
- BGP lobbies  
- TLS lobbies
- CDN lobbies
- AUTH lobbies
- ROLLBACK lobbies

Each episode is a self-contained investigation narrative with:
- Incident detection
- Evidence collection
- Pattern analysis
- Attribution attempts
- Resolution or escalation
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from .fsc import FailureDomain, FailureSeverity, FailureEvent
from .spine import append_event
from .quantum_rng import QuantumRNG, choice, random_float, random_int


class LobbyType(Enum):
    """Types of forensic lobbies."""
    DNS = "DNS"
    BGP = "BGP"
    TLS = "TLS"
    CDN = "CDN"
    AUTH = "AUTH"
    ROLLBACK = "ROLLBACK"


class EpisodePhase(Enum):
    """Phases of a forensic episode."""
    DETECTION = "detection"
    TRIAGE = "triage"
    INVESTIGATION = "investigation"
    ANALYSIS = "analysis"
    ATTRIBUTION = "attribution"
    RESOLUTION = "resolution"
    POSTMORTEM = "postmortem"


@dataclass
class Evidence:
    """A piece of forensic evidence."""
    evidence_id: str
    evidence_type: str
    source: str
    content: Any
    timestamp: float
    confidence: float = 1.0
    chain_of_custody: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.evidence_id:
            self.evidence_id = hashlib.sha256(
                f"{self.source}:{self.timestamp}:{self.content}".encode()
            ).hexdigest()[:12]


@dataclass
class ForensicEpisode:
    """A complete forensic episode."""
    episode_id: str
    lobby: LobbyType
    title: str
    phase: EpisodePhase
    start_time: float
    events: List[FailureEvent] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    suspects: Set[str] = field(default_factory=set)
    resolution: Optional[str] = None
    end_time: Optional[float] = None
    
    def __post_init__(self):
        if not self.episode_id:
            self.episode_id = hashlib.sha256(
                f"{self.lobby.value}:{self.start_time}:{self.title}".encode()
            ).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "lobby": self.lobby.value,
            "title": self.title,
            "phase": self.phase.value,
            "start_time": self.start_time,
            "event_count": len(self.events),
            "evidence_count": len(self.evidence),
            "suspects": list(self.suspects),
            "resolution": self.resolution,
            "duration": (self.end_time or time.time()) - self.start_time
        }


class EpisodeGenerator:
    """Generate forensic episode content."""
    
    # Incident templates by lobby
    INCIDENT_TEMPLATES = {
        LobbyType.DNS: [
            "Unexpected DNS resolution for {domain}",
            "DNS cache poisoning detected on {server}",
            "Zone transfer anomaly from {source}",
            "DDoS against DNS infrastructure",
            "Suspicious TXT record modifications"
        ],
        LobbyType.BGP: [
            "Route hijack announcement for {prefix}",
            "BGP session flapping on {peer}",
            "Unusual AS path for {destination}",
            "Prefix leak from {asn}",
            "BGP attribute manipulation detected"
        ],
        LobbyType.TLS: [
            "Certificate mismatch on {host}",
            "TLS downgrade attack detected",
            "Suspicious certificate chain from {issuer}",
            "Cipher suite anomaly in handshake",
            "Certificate transparency log discrepancy"
        ],
        LobbyType.CDN: [
            "Cache poisoning on {edge}",
            "Origin failover anomaly",
            "Geographic routing manipulation",
            "Edge node compromise suspected",
            "Content integrity check failure"
        ],
        LobbyType.AUTH: [
            "Credential stuffing attack from {source}",
            "Privilege escalation attempt on {account}",
            "Suspicious token generation pattern",
            "MFA bypass attempt detected",
            "Session hijacking indicators"
        ],
        LobbyType.ROLLBACK: [
            "State desync detected at tick {tick}",
            "Snapshot integrity failure",
            "Input replay anomaly",
            "Rewind window exceeded",
            "Determinism violation in replay"
        ]
    }
    
    # Evidence types by lobby
    EVIDENCE_TYPES = {
        LobbyType.DNS: ["query_log", "zone_file", "cache_dump", "packet_capture"],
        LobbyType.BGP: ["route_table", "update_log", "peer_session", "looking_glass"],
        LobbyType.TLS: ["certificate", "handshake_log", "key_exchange", "ct_log"],
        LobbyType.CDN: ["cache_log", "origin_request", "edge_metric", "purge_log"],
        LobbyType.AUTH: ["access_log", "token_audit", "session_log", "policy_check"],
        LobbyType.ROLLBACK: ["snapshot", "input_log", "state_hash", "tick_record"]
    }
    
    # Suspect pools
    SUSPECT_POOLS = {
        "nation_state": ["APT29", "APT28", "Lazarus", "EquationGroup"],
        "criminal": ["REvil", "DarkSide", "Conti", "LockBit"],
        "hacktivist": ["Anonymous", "LulzSec", "GhostSec"],
        "insider": ["disgruntled_employee", "compromised_account"],
        "unknown": ["unknown_actor", "unattributed"]
    }
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
    
    def generate_incident(self, lobby: LobbyType) -> Tuple[str, Dict[str, Any]]:
        """Generate an incident description and context."""
        template = choice(self.INCIDENT_TEMPLATES[lobby])
        
        # Fill in template variables
        context = {
            "domain": choice(["example.com", "target.org", "service.net"]),
            "server": choice(["ns1", "ns2", "resolver"]),
            "source": choice(["192.168.1.1", "10.0.0.1", "external"]),
            "prefix": choice(["192.0.2.0/24", "198.51.100.0/24"]),
            "peer": choice(["AS64512", "AS64513"]),
            "destination": choice(["8.8.8.8", "1.1.1.1"]),
            "asn": choice(["AS12345", "AS67890"]),
            "host": choice(["api.example.com", "cdn.example.com"]),
            "issuer": choice(["Let's Encrypt", "DigiCert", "Sectigo"]),
            "edge": choice(["edge-01", "edge-02", "edge-03"]),
            "account": choice(["admin", "service", "api"]),
            "tick": random_int(1000, 100000)
        }
        
        incident = template.format(**context)
        return incident, context
    
    def generate_evidence(self, lobby: LobbyType, incident: str) -> Evidence:
        """Generate evidence for an incident."""
        evidence_type = choice(self.EVIDENCE_TYPES[lobby])
        
        content_templates = {
            "query_log": {"queries": random_int(100, 10000), "unique_domains": random_int(10, 500)},
            "packet_capture": {"packets": random_int(1000, 100000), "size_mb": random_float() * 100},
            "certificate": {"subject": "CN=example.com", "issuer": "CN=Let's Encrypt", "valid": random_float() > 0.3},
            "snapshot": {"tick": random_int(1, 100000), "entities": random_int(10, 100), "hash": hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}
        }
        
        content = content_templates.get(evidence_type, {"raw": "binary_data"})
        
        return Evidence(
            evidence_id="",
            evidence_type=evidence_type,
            source=lobby.value,
            content=content,
            timestamp=time.time() - random_float() * 3600,  # Within last hour
            confidence=0.5 + random_float() * 0.5
        )
    
    def generate_suspects(self, evidence: List[Evidence]) -> Set[str]:
        """Generate suspects based on evidence."""
        suspects = set()
        
        # Determine suspect category based on evidence sophistication
        avg_confidence = sum(e.confidence for e in evidence) / len(evidence) if evidence else 0.5
        
        if avg_confidence > 0.8:
            category = choice(["nation_state", "criminal"])
        elif avg_confidence > 0.5:
            category = choice(["criminal", "hacktivist"])
        else:
            category = choice(["unknown", "insider"])
        
        num_suspects = random_int(1, 3)
        for _ in range(num_suspects):
            suspects.add(choice(self.SUSPECT_POOLS[category]))
        
        return suspects


class PlayForeverEngine:
    """Main engine for infinite forensic episode generation."""
    
    def __init__(self, spine_path: Optional[Path] = None):
        self.spine_path = spine_path or Path("play_forever_spine.jsonl")
        self.generator = EpisodeGenerator()
        self.active_episodes: Dict[str, ForensicEpisode] = {}
        self.completed_episodes: List[ForensicEpisode] = []
        self.episode_counter = 0
        self.rng = QuantumRNG()
    
    def create_episode(self, lobby: Optional[LobbyType] = None) -> ForensicEpisode:
        """Create a new forensic episode."""
        lobby = lobby or choice(list(LobbyType))
        
        # Generate incident
        incident, context = self.generator.generate_incident(lobby)
        
        # Create episode
        self.episode_counter += 1
        episode = ForensicEpisode(
            episode_id=f"",
            lobby=lobby,
            title=f"EP-{self.episode_counter:04d}: {incident[:50]}",
            phase=EpisodePhase.DETECTION,
            start_time=time.time(),
            events=[
                FailureEvent(
                    event_id="",
                    domain=FailureDomain[lobby.value],
                    severity=FailureSeverity.DEGRADED,
                    description=incident,
                    timestamp=time.time(),
                    context=context
                )
            ]
        )
        
        self.active_episodes[episode.episode_id] = episode
        
        # Log episode start
        self._log_event("episode_start", episode.to_dict())
        
        return episode
    
    def advance_episode(self, episode_id: str) -> Optional[ForensicEpisode]:
        """Advance an episode to next phase."""
        if episode_id not in self.active_episodes:
            return None
        
        episode = self.active_episodes[episode_id]
        
        # Advance phase
        phases = list(EpisodePhase)
        current_idx = phases.index(episode.phase)
        
        if current_idx < len(phases) - 1:
            episode.phase = phases[current_idx + 1]
            
            # Phase-specific actions
            if episode.phase == EpisodePhase.INVESTIGATION:
                # Generate evidence
                for _ in range(random_int(2, 5)):
                    evidence = self.generator.generate_evidence(episode.lobby, episode.title)
                    episode.evidence.append(evidence)
            
            elif episode.phase == EpisodePhase.ATTRIBUTION:
                # Generate suspects
                episode.suspects = self.generator.generate_suspects(episode.evidence)
            
            elif episode.phase == EpisodePhase.RESOLUTION:
                # Determine resolution
                if random_float() > 0.3:
                    episode.resolution = choice([
                        "Contained and remediated",
                        "Escalated to law enforcement",
                        "Attribution confirmed",
                        "False positive - closed"
                    ])
                else:
                    episode.resolution = "Ongoing monitoring - unresolved"
            
            # Log phase change
            self._log_event("episode_phase", {
                "episode_id": episode_id,
                "phase": episode.phase.value,
                "evidence_count": len(episode.evidence),
                "suspects": list(episode.suspects)
            })
        
        else:
            # Complete episode
            episode.end_time = time.time()
            self.completed_episodes.append(episode)
            del self.active_episodes[episode_id]
            
            # Log completion
            self._log_event("episode_complete", episode.to_dict())
        
        return episode
    
    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log event to spine."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            **data
        }
        append_event(self.spine_path, event)
    
    def generate_episodes(self, count: Optional[int] = None) -> Iterator[ForensicEpisode]:
        """Generate episodes indefinitely or up to count."""
        generated = 0
        
        while count is None or generated < count:
            # Create new episode
            episode = self.create_episode()
            generated += 1
            
            # Advance through all phases
            while episode.episode_id in self.active_episodes:
                self.advance_episode(episode.episode_id)
                yield episode
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        lobby_counts = {}
        for ep in self.completed_episodes:
            lobby_counts[ep.lobby.value] = lobby_counts.get(ep.lobby.value, 0) + 1
        
        return {
            "active_episodes": len(self.active_episodes),
            "completed_episodes": len(self.completed_episodes),
            "lobby_distribution": lobby_counts,
            "resolution_rate": sum(
                1 for ep in self.completed_episodes
                if ep.resolution and "resolved" in ep.resolution.lower()
            ) / len(self.completed_episodes) if self.completed_episodes else 0
        }


# Convenience functions
_engine: Optional[PlayForeverEngine] = None


def initialize(spine_path: Optional[Path] = None) -> PlayForeverEngine:
    """Initialize global Play Forever engine."""
    global _engine
    _engine = PlayForeverEngine(spine_path)
    return _engine


def get_engine() -> PlayForeverEngine:
    """Get global Play Forever engine."""
    if _engine is None:
        return initialize()
    return _engine
