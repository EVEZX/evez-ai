"""Truth-Sifting Intent-Asset Bundler with Camouflage.

Implements:
- Intent detection and classification
- Asset bundling with truth verification
- Camouflage generation for protection
- Multi-layered truth verification
- Adversarial intent neutralization
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .quantum_rng import QuantumRNG, random_bytes, random_float
from .spine import append_event


class IntentType(Enum):
    """Types of detected intents."""
    BENIGN = auto()
    INFORMATIONAL = auto()
    OPERATIONAL = auto()
    ADVERSARIAL = auto()
    DECEPTIVE = auto()
    MALICIOUS = auto()
    UNKNOWN = auto()


class AssetType(Enum):
    """Types of assets that can be bundled."""
    DATA = auto()
    CODE = auto()
    CONFIG = auto()
    CREDENTIAL = auto()
    KEY = auto()
    STATE = auto()
    LOG = auto()


@dataclass
class Intent:
    """A detected intent."""
    intent_type: IntentType
    confidence: float
    source: str
    indicators: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def is_adversarial(self) -> bool:
        return self.intent_type in (
            IntentType.ADVERSARIAL,
            IntentType.DECEPTIVE,
            IntentType.MALICIOUS
        )


@dataclass
class Asset:
    """A bundle-able asset."""
    asset_id: str
    asset_type: AssetType
    content: Any
    sensitivity: float  # 0.0 to 1.0
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """Compute asset checksum."""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha3_256(content_str.encode()).hexdigest()[:32]
    
    def verify(self) -> bool:
        """Verify asset integrity."""
        return self.checksum == self._compute_checksum()


@dataclass
class Bundle:
    """A bundle of assets with truth verification."""
    bundle_id: str
    assets: Dict[str, Asset] = field(default_factory=dict)
    intent_classification: IntentType = IntentType.UNKNOWN
    trust_score: float = 0.5
    camouflage_layer: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    verified: bool = False
    
    def __post_init__(self):
        if not self.bundle_id:
            self.bundle_id = hashlib.sha256(
                f"{self.created_at}:{len(self.assets)}".encode()
            ).hexdigest()[:16]
    
    def add_asset(self, asset: Asset) -> None:
        """Add asset to bundle."""
        self.assets[asset.asset_id] = asset
        self._update_trust_score()
    
    def _update_trust_score(self) -> None:
        """Update bundle trust score based on assets."""
        if not self.assets:
            self.trust_score = 0.5
            return
        
        # Average sensitivity (lower is more trusted)
        avg_sensitivity = sum(a.sensitivity for a in self.assets.values()) / len(self.assets)
        
        # Verify all assets
        all_verified = all(a.verify() for a in self.assets.values())
        
        self.trust_score = (1.0 - avg_sensitivity) * (1.0 if all_verified else 0.5)
    
    def verify_integrity(self) -> bool:
        """Verify bundle integrity."""
        self.verified = all(asset.verify() for asset in self.assets.values())
        return self.verified


class IntentAnalyzer:
    """Analyze and classify intents from various sources."""
    
    # Intent indicators
    ADVERSARIAL_PATTERNS = [
        r"(?i)(exploit|vulnerability|cve-\d{4}-\d+)",
        r"(?i)(bypass|circumvent|evade)",
        r"(?i)(injection|overflow|ransomware)",
        r"(?i)(backdoor|rootkit|trojan)",
        r"(?i)(phish|spearphish|social.engineering)"
    ]
    
    DECEPTIVE_PATTERNS = [
        r"(?i)(misleading|false|fabricated)",
        r"(?i)(impersonat|spoof|fake)",
        r"(?i)(deepfake|synthetic|generated)"
    ]
    
    OPERATIONAL_PATTERNS = [
        r"(?i)(deploy|execute|implement)",
        r"(?i)(configure|setup|install)",
        r"(?i)(monitor|observe|track)"
    ]
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.pattern_scores: Dict[str, float] = {}
    
    def analyze_text(self, text: str, source: str = "unknown") -> Intent:
        """Analyze text for intent indicators."""
        indicators = []
        scores = {
            IntentType.ADVERSARIAL: 0.0,
            IntentType.DECEPTIVE: 0.0,
            IntentType.OPERATIONAL: 0.0,
            IntentType.BENIGN: 0.5  # Base score
        }
        
        # Check adversarial patterns
        for pattern in self.ADVERSARIAL_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                scores[IntentType.ADVERSARIAL] += len(matches) * 0.2
                indicators.extend(matches[:3])
        
        # Check deceptive patterns
        for pattern in self.DECEPTIVE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                scores[IntentType.DECEPTIVE] += len(matches) * 0.25
                indicators.extend(matches[:3])
        
        # Check operational patterns
        for pattern in self.OPERATIONAL_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                scores[IntentType.OPERATIONAL] += len(matches) * 0.15
                indicators.extend(matches[:3])
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        # Select highest scoring intent
        intent_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[intent_type]
        
        return Intent(
            intent_type=intent_type,
            confidence=confidence,
            source=source,
            indicators=list(set(indicators))[:5],
            context={"text_length": len(text), "word_count": len(text.split())}
        )
    
    def analyze_behavior(self, actions: List[Dict[str, Any]], source: str = "unknown") -> Intent:
        """Analyze behavior patterns for intent."""
        indicators = []
        
        # Check for suspicious patterns
        rapid_actions = len(actions) > 10  # Many actions in short time
        unusual_sequence = False  # Actions in unusual order
        privilege_escalation = False
        
        for i, action in enumerate(actions):
            action_type = action.get("type", "")
            
            if "escalate" in action_type or "elevate" in action_type:
                privilege_escalation = True
                indicators.append("privilege_escalation")
            
            if "access" in action_type and i > 0:
                prev = actions[i-1].get("type", "")
                if "auth" not in prev and "login" not in prev:
                    unusual_sequence = True
                    indicators.append("unauthorized_access_pattern")
        
        # Determine intent
        if privilege_escalation or (rapid_actions and unusual_sequence):
            intent_type = IntentType.ADVERSARIAL
            confidence = 0.7 + (0.1 if privilege_escalation else 0) + (0.1 if rapid_actions else 0)
        elif rapid_actions:
            intent_type = IntentType.OPERATIONAL
            confidence = 0.6
        else:
            intent_type = IntentType.BENIGN
            confidence = 0.7
        
        return Intent(
            intent_type=intent_type,
            confidence=min(0.95, confidence),
            source=source,
            indicators=indicators,
            context={"action_count": len(actions), "rapid_actions": rapid_actions}
        )


class CamouflageEngine:
    """Generate camouflage for asset protection."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
    
    def generate_camouflage(self, bundle: Bundle, level: int = 1) -> str:
        """Generate camouflage layer for bundle.
        
        Levels:
        1: Basic obfuscation
        2: Structural mimicry
        3: Behavioral camouflage
        """
        if level == 1:
            return self._basic_obfuscation(bundle)
        elif level == 2:
            return self._structural_mimicry(bundle)
        else:
            return self._behavioral_camouflage(bundle)
    
    def _basic_obfuscation(self, bundle: Bundle) -> str:
        """Basic XOR obfuscation."""
        key = random_bytes(32)
        bundle_data = json.dumps({
            "id": bundle.bundle_id,
            "assets": len(bundle.assets)
        }).encode()
        
        obfuscated = bytes(b ^ key[i % len(key)] for i, b in enumerate(bundle_data))
        return f"obf:v1:{key.hex()}:{obfuscated.hex()}"
    
    def _structural_mimicry(self, bundle: Bundle) -> str:
        """Mimic common data structures."""
        # Mimic a common JSON structure
        mimic = {
            "status": "ok",
            "timestamp": time.time(),
            "data": {
                "items": list(range(len(bundle.assets))),
                "meta": {"version": "1.0", "source": "internal"}
            }
        }
        
        # Embed actual bundle data in seemingly random field
        actual_data = hashlib.sha256(
            json.dumps({k: v.content for k, v in bundle.assets.items()}, sort_keys=True).encode()
        ).hexdigest()
        
        mimic["data"]["checksum"] = actual_data[:16]
        
        return f"mimic:json:{json.dumps(mimic)}"
    
    def _behavioral_camouflage(self, bundle: Bundle) -> str:
        """Camouflage that mimics normal system behavior."""
        # Generate fake log entries that blend real data
        logs = []
        for i in range(random_int(5, 15)):
            logs.append({
                "level": choice(["INFO", "DEBUG", "TRACE"]),
                "message": f"Processed item {i}",
                "timestamp": time.time() - random_float() * 60
            })
        
        # Embed bundle reference in one log
        if logs:
            logs[0]["trace_id"] = bundle.bundle_id[:8]
        
        return f"camo:log:{json.dumps(logs)}"
    
    def verify_camouflage(self, camouflage: str, bundle: Bundle) -> bool:
        """Verify that camouflage belongs to bundle."""
        if not camouflage or not bundle:
            return False
        
        # Extract and verify
        if camouflage.startswith("obf:"):
            return bundle.bundle_id in camouflage
        elif camouflage.startswith("mimic:"):
            return bundle.bundle_id[:8] in camouflage
        elif camouflage.startswith("camo:"):
            return bundle.bundle_id[:8] in camouflage
        
        return False


class TruthSifter:
    """Main truth-sifting engine."""
    
    def __init__(self, spine_path = None):
        from pathlib import Path
        self.spine_path = spine_path or Path("truth_sifter_spine.jsonl")
        self.intent_analyzer = IntentAnalyzer()
        self.camouflage_engine = CamouflageEngine()
        self.bundles: Dict[str, Bundle] = {}
        self.intent_history: List[Intent] = []
        self.truth_cache: Dict[str, bool] = {}
    
    def sift(self, content: Any, content_type: str = "text", source: str = "unknown") -> Tuple[Intent, Bundle]:
        """Sift content for truth and create bundle."""
        # Analyze intent
        if content_type == "text":
            intent = self.intent_analyzer.analyze_text(str(content), source)
        elif content_type == "behavior":
            intent = self.intent_analyzer.analyze_behavior(content, source)
        else:
            intent = Intent(IntentType.UNKNOWN, 0.5, source)
        
        self.intent_history.append(intent)
        
        # Create asset from content
        asset_type = AssetType.DATA
        if content_type == "code":
            asset_type = AssetType.CODE
        elif content_type == "config":
            asset_type = AssetType.CONFIG
        
        asset = Asset(
            asset_id=hashlib.sha256(f"{source}:{time.time()}".encode()).hexdigest()[:12],
            asset_type=asset_type,
            content=content,
            sensitivity=0.7 if intent.is_adversarial() else 0.3,
            metadata={"intent_type": intent.intent_type.name, "confidence": intent.confidence}
        )
        
        # Create bundle
        bundle = Bundle(
            bundle_id="",
            intent_classification=intent.intent_type,
            trust_score=1.0 - intent.confidence if intent.is_adversarial() else 0.5 + intent.confidence * 0.5
        )
        bundle.add_asset(asset)
        
        # Apply camouflage if adversarial
        if intent.is_adversarial():
            bundle.camouflage_layer = self.camouflage_engine.generate_camouflage(bundle, level=2)
        
        # Store bundle
        self.bundles[bundle.bundle_id] = bundle
        
        # Log to spine
        self._log_sifting(intent, bundle)
        
        return intent, bundle
    
    def _log_sifting(self, intent: Intent, bundle: Bundle) -> None:
        """Log sifting event to spine."""
        event = {
            "type": "truth_sift",
            "intent_type": intent.intent_type.name,
            "confidence": intent.confidence,
            "bundle_id": bundle.bundle_id,
            "trust_score": bundle.trust_score,
            "camouflaged": bundle.camouflage_layer is not None,
            "timestamp": time.time()
        }
        append_event(self.spine_path, event)
    
    def verify_bundle(self, bundle_id: str) -> bool:
        """Verify a bundle's integrity."""
        if bundle_id not in self.bundles:
            return False
        
        bundle = self.bundles[bundle_id]
        
        # Check cache
        if bundle_id in self.truth_cache:
            return self.truth_cache[bundle_id]
        
        # Verify
        result = bundle.verify_integrity()
        
        # Verify camouflage if present
        if bundle.camouflage_layer:
            result = result and self.camouflage_engine.verify_camouflage(
                bundle.camouflage_layer, bundle
            )
        
        self.truth_cache[bundle_id] = result
        return result
    
    def get_threat_assessment(self) -> Dict[str, Any]:
        """Get threat assessment from intent history."""
        if not self.intent_history:
            return {"status": "no_data"}
        
        # Count by type
        type_counts = {}
        for intent in self.intent_history:
            type_counts[intent.intent_type.name] = type_counts.get(intent.intent_type.name, 0) + 1
        
        # Calculate threat score
        adversarial_count = sum(
            1 for i in self.intent_history
            if i.is_adversarial()
        )
        threat_score = adversarial_count / len(self.intent_history)
        
        return {
            "total_analyzed": len(self.intent_history),
            "intent_distribution": type_counts,
            "threat_score": threat_score,
            "adversarial_count": adversarial_count,
            "status": "CRITICAL" if threat_score > 0.5 else "ELEVATED" if threat_score > 0.2 else "NORMAL"
        }


# Convenience functions
_sifter: Optional[TruthSifter] = None


def initialize(spine_path = None) -> TruthSifter:
    """Initialize global truth sifter."""
    global _sifter
    _sifter = TruthSifter(spine_path)
    return _sifter


def get_sifter() -> TruthSifter:
    """Get global truth sifter."""
    if _sifter is None:
        return initialize()
    return _sifter


def sift(content: Any, content_type: str = "text", source: str = "unknown") -> Tuple[Intent, Bundle]:
    """Sift content for truth."""
    return get_sifter().sift(content, content_type, source)
