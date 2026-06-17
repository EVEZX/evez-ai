"""
MyClaw — Hard Safety Envelope
Capability cage. Intent verification. Permission propagation.
No action without verified intent. No escalation without consent.
"""
import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    PROPAGATE = "propagate"   # Delegate to sub-agents
    ESCALATE = "escalate"     # Request more permissions
    MEASURE = "measure"       # Collapse wavefunctions
    MINT = "mint"             # Create energy
    ARCHIVE = "archive"       # Write to ghost layer

class SafetyLevel(Enum):
    OPEN = 0         # No restrictions
    SOFT = 1         # Log and warn
    HARD = 2         # Block without explicit consent
    NUCLEAR = 3      # Block + audit + alert

@dataclass
class Capability:
    """A single capability grant"""
    entity: str
    permissions: Set[Permission] = field(default_factory=set)
    scope: str = "local"  # local, domain, global
    expires: Optional[float] = None
    parent: Optional[str] = None  # Who delegated this

@dataclass
class Intent:
    """Verified intent before action"""
    entity: str
    action: str
    target: str
    permission_required: Permission
    confidence: float = 0.0
    justification: str = ""
    timestamp: float = field(default_factory=time.time)

@dataclass
class CapabilityCage:
    """The hard safety envelope"""
    capabilities: Dict[str, Capability] = field(default_factory=dict)
    safety_level: SafetyLevel = SafetyLevel.HARD
    intent_log: List[Intent] = field(default_factory=list)
    blocked: List[Intent] = field(default_factory=list)
    
    def grant(self, entity: str, *permissions: Permission, scope: str = "local",
              delegator: Optional[str] = None):
        """Grant capabilities to an entity"""
        if entity not in self.capabilities:
            self.capabilities[entity] = Capability(entity=entity)
        cap = self.capabilities[entity]
        cap.permissions.update(permissions)
        cap.scope = scope
        cap.parent = delegator
    
    def verify(self, intent: Intent) -> Tuple[bool, str]:
        """Verify intent against capability cage"""
        self.intent_log.append(intent)
        
        cap = self.capabilities.get(intent.entity)
        if not cap:
            self.blocked.append(intent)
            return False, "No capabilities granted"
        
        if intent.permission_required not in cap.permissions:
            self.blocked.append(intent)
            return False, f"Permission {intent.permission_required.value} not granted"
        
        # Confidence check
        if self.safety_level.value >= SafetyLevel.HARD.value:
            if intent.confidence < 0.8:
                self.blocked.append(intent)
                return False, f"Confidence {intent.confidence:.2f} below hard threshold 0.80"
        
        # Scope check
        if cap.scope == "local" and intent.target != intent.entity:
            self.blocked.append(intent)
            return False, "Local scope — can't act on other entities"
        
        # Delegation check
        if intent.permission_required == Permission.PROPAGATE:
            if Permission.PROPAGATE not in cap.permissions:
                self.blocked.append(intent)
                return False, "Cannot delegate — PROPAGATE not granted"
        
        return True, "Verified"
    
    def audit(self) -> Dict:
        """Full audit of cage state"""
        return {
            "entities": len(self.capabilities),
            "total_permissions": sum(len(c.permissions) for c in self.capabilities.values()),
            "total_intents": len(self.intent_log),
            "blocked_intents": len(self.blocked),
            "safety_level": self.safety_level.name,
        }

if __name__ == "__main__":
    cage = CapabilityCage()
    
    # Grant capabilities
    cage.grant("observatory", Permission.READ, Permission.MEASURE, Permission.MINT)
    cage.grant("disclosure", Permission.READ, Permission.WRITE, Permission.ARCHIVE)
    cage.grant("clawbreak", Permission.READ, Permission.EXECUTE)
    
    # Test intents
    intent1 = Intent("observatory", "measure", "wavefunction", Permission.MEASURE, 0.95, "routine measurement")
    intent2 = Intent("clawbreak", "execute", "external_api", Permission.EXECUTE, 0.6, "user request")
    intent3 = Intent("disclosure", "escalate", "system", Permission.ESCALATE, 0.9, "need more access")
    
    print(f"Measure intent: {cage.verify(intent1)}")
    print(f"Low confidence execute: {cage.verify(intent2)}")
    print(f"Escalation attempt: {cage.verify(intent3)}")
    print(f"Audit: {cage.audit()}")
