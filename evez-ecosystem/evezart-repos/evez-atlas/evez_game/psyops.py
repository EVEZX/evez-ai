"""Counter-Intelligence PsyOps Module.

Implements psychological operations for:
- Adversary deception and misdirection
- Honeypot deployment and monitoring
- False flag operations
- Narrative control and influence
- Cognitive disruption of attackers
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from .quantum_rng import QuantumRNG, choice, random_float, random_int, shuffle
from .spine import append_event
from .truth_sifter import IntentType


class PsyOpType(Enum):
    """Types of psychological operations."""
    DECEPTION = auto()      # False information
    MISDIRECTION = auto()   # Lead away from real targets
    HONEYPOT = auto()       # Attractive false target
    FALSE_FLAG = auto()     # Attribute to wrong actor
    NARRATIVE = auto()      # Shape perception
    COGNITIVE = auto()      # Disrupt thinking
    MIMICRY = auto()        # Imitate legitimate systems


class TargetProfile(Enum):
    """Types of targets for psyops."""
    SCRIPT_KIDDIE = auto()
    CRIMINAL_GROUP = auto()
    NATION_STATE = auto()
    INSIDER = auto()
    AUTOMATED = auto()
    UNKNOWN = auto()


@dataclass
class Honeypot:
    """A deployed honeypot."""
    honeypot_id: str
    honeypot_type: str
    deployment_target: str
    attractiveness: float  # 0.0 to 1.0
    detection_sensitivity: float
    deployed_at: float = field(default_factory=time.time)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    compromised: bool = False
    
    def record_interaction(self, source: str, action: str, data: Dict[str, Any]) -> None:
        """Record an interaction with the honeypot."""
        self.interactions.append({
            "timestamp": time.time(),
            "source": source,
            "action": action,
            "data": data
        })
        
        # Check for compromise indicators
        if action in ("exploit", "escalate", "persist"):
            self.compromised = True


@dataclass
class DeceptionCampaign:
    """An active deception campaign."""
    campaign_id: str
    psyop_type: PsyOpType
    target_profile: TargetProfile
    narrative: str
    assets: List[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def end(self, success: bool = True) -> None:
        """End the campaign."""
        self.ended_at = time.time()
        self.success_metrics["success"] = success
        self.success_metrics["duration"] = self.ended_at - self.started_at


@dataclass
class FalseFlag:
    """A false flag operation."""
    flag_id: str
    fake_attribution: str
    real_attribution: str
    cover_story: str
    evidence_planted: List[str] = field(default_factory=list)
    deployed_at: float = field(default_factory=time.time)
    
    def plant_evidence(self, evidence_type: str, content: Any) -> str:
        """Plant false evidence."""
        evidence_id = hashlib.sha256(
            f"{self.flag_id}:{evidence_type}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        self.evidence_planted.append(evidence_id)
        return evidence_id


class HoneypotManager:
    """Manage honeypot deployment and monitoring."""
    
    HONEYPOT_TYPES = [
        "ssh_server",
        "web_application",
        "database",
        "api_endpoint",
        "file_share",
        "container_registry"
    ]
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.honeypots: Dict[str, Honeypot] = {}
        self.interaction_log: List[Dict[str, Any]] = []
    
    def deploy(self, target_environment: str, honeypot_type: Optional[str] = None) -> Honeypot:
        """Deploy a new honeypot."""
        hp_type = honeypot_type or choice(self.HONEYPOT_TYPES)
        
        honeypot = Honeypot(
            honeypot_id=hashlib.sha256(
                f"{hp_type}:{target_environment}:{time.time()}".encode()
            ).hexdigest()[:12],
            honeypot_type=hp_type,
            deployment_target=target_environment,
            attractiveness=0.5 + random_float() * 0.5,
            detection_sensitivity=0.3 + random_float() * 0.7
        )
        
        self.honeypots[honeypot.honeypot_id] = honeypot
        
        return honeypot
    
    def deploy_quantum_camouflaged(self, target: str) -> Honeypot:
        """Deploy honeypot with quantum-random camouflage."""
        # Generate random appearance
        appearance = choice(self.HONEYPOT_TYPES)
        
        # But actual type is different
        actual_types = [t for t in self.HONEYPOT_TYPES if t != appearance]
        actual_type = choice(actual_types)
        
        honeypot = self.deploy(target, actual_type)
        
        # Add camouflage metadata
        honeypot.attractiveness *= 1.2  # More attractive due to camouflage
        
        return honeypot
    
    def analyze_interactions(self, honeypot_id: str) -> Dict[str, Any]:
        """Analyze interactions with a honeypot."""
        if honeypot_id not in self.honeypots:
            return {"error": "Honeypot not found"}
        
        hp = self.honeypots[honeypot_id]
        
        if not hp.interactions:
            return {"status": "no_interactions"}
        
        # Analyze patterns
        sources = set(i["source"] for i in hp.interactions)
        actions = [i["action"] for i in hp.interactions]
        
        action_counts = {}
        for action in actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Determine sophistication
        sophisticated_actions = {"exploit", "escalate", "persist", "lateral_move"}
        sophistication = sum(1 for a in actions if a in sophisticated_actions) / len(actions)
        
        return {
            "honeypot_id": honeypot_id,
            "interaction_count": len(hp.interactions),
            "unique_sources": len(sources),
            "action_breakdown": action_counts,
            "compromised": hp.compromised,
            "sophistication_score": sophistication,
            "target_profile": self._classify_target(sophistication)
        }
    
    def _classify_target(self, sophistication: float) -> str:
        """Classify target based on sophistication."""
        if sophistication > 0.7:
            return "nation_state"
        elif sophistication > 0.4:
            return "criminal_group"
        elif sophistication > 0.1:
            return "script_kiddie"
        else:
            return "automated"
    
    def get_high_value_targets(self) -> List[str]:
        """Get honeypots with significant interactions."""
        return [
            hp_id for hp_id, hp in self.honeypots.items()
            if len(hp.interactions) > 10 or hp.compromised
        ]


class DeceptionEngine:
    """Generate and manage deceptive content."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.active_campaigns: Dict[str, DeceptionCampaign] = {}
        self.false_flags: Dict[str, FalseFlag] = {}
    
    def launch_campaign(self, psyop_type: PsyOpType, target: TargetProfile,
                       narrative: str) -> DeceptionCampaign:
        """Launch a deception campaign."""
        campaign = DeceptionCampaign(
            campaign_id=hashlib.sha256(
                f"{psyop_type.name}:{target.name}:{time.time()}".encode()
            ).hexdigest()[:12],
            psyop_type=psyop_type,
            target_profile=target,
            narrative=narrative
        )
        
        self.active_campaigns[campaign.campaign_id] = campaign
        
        return campaign
    
    def create_false_flag(self, fake_attribution: str, real_attribution: str,
                         cover_story: str) -> FalseFlag:
        """Create a false flag operation."""
        flag = FalseFlag(
            flag_id=hashlib.sha256(
                f"{fake_attribution}:{time.time()}".encode()
            ).hexdigest()[:12],
            fake_attribution=fake_attribution,
            real_attribution=real_attribution,
            cover_story=cover_story
        )
        
        self.false_flags[flag.flag_id] = flag
        
        return flag
    
    def generate_deceptive_log(self, fake_attribution: str, 
                               technique: str = "generic") -> Dict[str, Any]:
        """Generate deceptive log entries."""
        timestamps = sorted([
            time.time() - random_float() * 86400
            for _ in range(random_int(5, 20))
        ])
        
        log_entries = []
        for ts in timestamps:
            entry = {
                "timestamp": ts,
                "source_ip": f"10.{random_int(0,255)}.{random_int(0,255)}.{random_int(0,255)}",
                "user_agent": choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "curl/7.68.0",
                    "python-requests/2.25.1"
                ]),
                "action": choice(["login", "query", "download", "upload"]),
                "status": choice([200, 200, 200, 401, 403, 500]),
                "technique_indicator": technique if random_float() > 0.7 else ""
            }
            log_entries.append(entry)
        
        # Add attribution markers
        for entry in log_entries[:3]:
            entry["attribution_marker"] = hashlib.sha256(
                fake_attribution.encode()
            ).hexdigest()[:8]
        
        return {
            "attribution": fake_attribution,
            "entries": log_entries,
            "technique": technique
        }
    
    def generate_honeypot_content(self, honeypot_type: str) -> Dict[str, Any]:
        """Generate convincing honeypot content."""
        if honeypot_type == "ssh_server":
            return {
                "banner": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.1",
                "users": ["admin", "root", "ubuntu", "user"],
                "fake_files": ["/etc/passwd", "/home/admin/.ssh/id_rsa"],
                "tripwire_commands": ["cat /etc/shadow", "wget", "curl", "nc"]
            }
        elif honeypot_type == "web_application":
            return {
                "pages": ["/login", "/admin", "/api/v1/users", "/config"],
                "forms": {"username": "text", "password": "password"},
                "fake_data": {"users": random_int(10, 1000), "version": "2.4.1"}
            }
        elif honeypot_type == "database":
            return {
                "tables": ["users", "transactions", "sessions", "api_keys"],
                "fake_records": random_int(1000, 100000),
                "tripwire_queries": ["DROP", "DELETE", "UPDATE"]
            }
        
        return {"generic": True}


class CognitiveDisruption:
    """Cognitive disruption techniques for adversaries."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
    
    def generate_cognitive_load(self, intensity: float = 0.5) -> Dict[str, Any]:
        """Generate content designed to increase cognitive load."""
        techniques = []
        
        if intensity > 0.3:
            techniques.append("information_overload")
        if intensity > 0.5:
            techniques.append("contradictory_signals")
        if intensity > 0.7:
            techniques.append("time_pressure")
        if intensity > 0.9:
            techniques.append("paradoxical_constraints")
        
        return {
            "techniques": techniques,
            "intensity": intensity,
            "implementation": self._implement_cognitive_load(techniques)
        }
    
    def _implement_cognitive_load(self, techniques: List[str]) -> Dict[str, Any]:
        """Implement cognitive load techniques."""
        implementation = {}
        
        if "information_overload" in techniques:
            implementation["noise_generation"] = {
                "decoy_events_per_minute": random_int(10, 100),
                "false_positives": random_int(5, 20)
            }
        
        if "contradictory_signals" in techniques:
            implementation["signal_confusion"] = {
                "inconsistent_responses": True,
                "random_delays": [random_float() * 5 for _ in range(10)]
            }
        
        if "time_pressure" in techniques:
            implementation["artificial_deadlines"] = {
                "session_timeout": random_int(30, 120),
                "rate_limits": random_int(10, 100)
            }
        
        return implementation
    
    def generate_narrative_confusion(self, true_narrative: str) -> List[str]:
        """Generate confusing alternative narratives."""
        alternatives = [
            f"The {choice(['attack', 'incident', 'event'])} was actually {choice(['authorized', 'expected', 'a drill'])}",
            f"{choice(['No', 'Limited', 'Partial'])} {choice(['impact', 'damage', 'breach'])} occurred",
            f"Attribution points to {choice(['insider', 'competitor', 'nation-state', 'criminal group'])}",
            f"This is a {choice(['false flag', 'distraction', 'test'])} for {choice(['larger operation', 'future attack'])}",
            f"The {choice(['data', 'systems', 'network'])} was {choice(['already compromised', 'hardened', 'decoy'])}"
        ]
        
        shuffle(alternatives)
        return alternatives[:random_int(2, 4)]


class PsyOpsController:
    """Main controller for psyops operations."""
    
    def __init__(self, spine_path = None):
        from pathlib import Path
        self.spine_path = spine_path or Path("psyops_spine.jsonl")
        self.honeypots = HoneypotManager()
        self.deception = DeceptionEngine()
        self.disruption = CognitiveDisruption()
        self.operation_log: List[Dict[str, Any]] = []
        self.active_countermeasures: Set[str] = set()
    
    def deploy_countermeasure(self, intent_type: IntentType, 
                             source: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy appropriate countermeasure based on detected intent."""
        countermeasure = {
            "deployed_at": time.time(),
            "target": source,
            "trigger": intent_type.name
        }
        
        if intent_type == IntentType.ADVERSARIAL:
            # Deploy honeypot
            hp = self.honeypots.deploy_quantum_camouflaged(source)
            countermeasure["type"] = "honeypot"
            countermeasure["honeypot_id"] = hp.honeypot_id
            countermeasure["camouflage"] = True
        
        elif intent_type == IntentType.DECEPTIVE:
            # Launch deception campaign
            campaign = self.deception.launch_campaign(
                PsyOpType.DECEPTION,
                TargetProfile.UNKNOWN,
                "Counter-deception narrative"
            )
            countermeasure["type"] = "deception_campaign"
            countermeasure["campaign_id"] = campaign.campaign_id
        
        elif intent_type == IntentType.MALICIOUS:
            # Full cognitive disruption
            disruption = self.disruption.generate_cognitive_load(intensity=0.8)
            countermeasure["type"] = "cognitive_disruption"
            countermeasure["disruption"] = disruption
        
        else:
            # Basic misdirection
            countermeasure["type"] = "misdirection"
            countermeasure["redirect"] = choice(["/dev/null", "honeypot_zone", "monitoring"])
        
        self.active_countermeasures.add(countermeasure.get("honeypot_id") or 
                                        countermeasure.get("campaign_id") or 
                                        str(time.time()))
        
        # Log operation
        self._log_operation("countermeasure_deployed", countermeasure)
        
        return countermeasure
    
    def _log_operation(self, op_type: str, data: Dict[str, Any]) -> None:
        """Log psyops operation to spine."""
        event = {
            "type": op_type,
            "timestamp": time.time(),
            **data
        }
        append_event(self.spine_path, event)
        self.operation_log.append(event)
    
    def get_status(self) -> Dict[str, Any]:
        """Get psyops system status."""
        return {
            "honeypots_deployed": len(self.honeypots.honeypots),
            "active_campaigns": len(self.deception.active_campaigns),
            "false_flags": len(self.deception.false_flags),
            "active_countermeasures": len(self.active_countermeasures),
            "operations_logged": len(self.operation_log),
            "high_value_honeypots": self.honeypots.get_high_value_targets()
        }


# Convenience functions
_controller: Optional[PsyOpsController] = None


def initialize(spine_path = None) -> PsyOpsController:
    """Initialize global psyops controller."""
    global _controller
    _controller = PsyOpsController(spine_path)
    return _controller


def get_controller() -> PsyOpsController:
    """Get global psyops controller."""
    if _controller is None:
        return initialize()
    return _controller
