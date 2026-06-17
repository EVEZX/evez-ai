"""Self-Building Game Mechanics.

The game builds itself through:
- Procedural content generation based on player behavior
- Dynamic threat adaptation
- Emergent narrative from system interactions
- Self-modifying rule sets
- Recursive system enhancement
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from .spine import append_event
from .quantum_rng import QuantumRNG, choice, random_float, random_int
from .cognition_wheel import CognitiveStage, CognitiveWheel


class BuildTrigger(Enum):
    """Triggers for self-building behavior."""
    PLAYER_ACTION = auto()
    THREAT_DETECTED = auto()
    PATTERN_DETECTED = auto()
    COGNITION_ADVANCE = auto()
    TIME_BASED = auto()
    SYSTEM_STRESS = auto()


class BuildType(Enum):
    """Types of self-building content."""
    NEW_LOBBY = auto()
    NEW_RULE = auto()
    NEW_DEFENSE = auto()
    NEW_NARRATIVE = auto()
    NEW_CHALLENGE = auto()
    SYSTEM_ENHANCEMENT = auto()


@dataclass
class BuildEvent:
    """A self-building event."""
    build_id: str
    trigger: BuildTrigger
    build_type: BuildType
    description: str
    timestamp: float
    parent_build: Optional[str] = None
    child_builds: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.build_id:
            self.build_id = hashlib.sha256(
                f"{self.trigger.name}:{self.build_type.name}:{self.timestamp}".encode()
            ).hexdigest()[:16]


@dataclass
class GameRule:
    """A dynamic game rule."""
    rule_id: str
    condition: str
    action: str
    priority: int
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    activation_count: int = 0
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate rule condition against context."""
        try:
            # Simple condition evaluation
            if "threat_level" in self.condition:
                match = eval(self.condition, {"__builtins__": {}}, context)
                return match
            return False
        except Exception:
            return False


@dataclass
class Lobby:
    """A game lobby/environment."""
    lobby_id: str
    lobby_type: str
    rules: List[GameRule] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)
    difficulty: float = 0.5
    created_at: float = field(default_factory=time.time)
    
    def add_rule(self, rule: GameRule) -> None:
        """Add a rule to the lobby."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)


class ProceduralContentGenerator:
    """Generate procedural game content."""
    
    LOBBY_TEMPLATES = [
        "{adjective} {noun} {location}",
        "{noun} of {concept}",
        "The {adjective} {noun}",
        "{location} of {adjective} {noun}"
    ]
    
    ADJECTIVES = ["Hidden", "Forbidden", "Ancient", "Digital", "Quantum", "Shadow", "Crystal", "Neural"]
    NOUNS = ["Archive", "Protocol", "Firewall", "Gateway", "Matrix", "Core", "Nexus", "Construct"]
    CONCEPTS = ["Entropy", "Truth", "Deception", "Knowledge", "Power", "Chaos", "Order"]
    LOCATIONS = ["Sector", "Zone", "Domain", "Realm", "Layer", "Plane"]
    
    CHALLENGE_TEMPLATES = [
        "Decrypt the {target} within {time} seconds",
        "Navigate the {obstacle} without triggering {alert}",
        "Identify {count} hidden {items} in the {location}",
        "Synchronize with the {system} before {event}"
    ]
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
    
    def generate_lobby_name(self) -> str:
        """Generate a procedural lobby name."""
        template = choice(self.LOBBY_TEMPLATES)
        return template.format(
            adjective=choice(self.ADJECTIVES),
            noun=choice(self.NOUNS),
            concept=choice(self.CONCEPTS),
            location=choice(self.LOCATIONS)
        )
    
    def generate_challenge(self, difficulty: float = 0.5) -> Dict[str, Any]:
        """Generate a procedural challenge."""
        template = choice(self.CHALLENGE_TEMPLATES)
        
        challenge = {
            "description": template.format(
                target=choice(self.NOUNS).lower(),
                time=random_int(10, 300),
                obstacle=choice(["firewall", "maze", "trap"]),
                alert=choice(["alarm", "lockdown", "trace"]),
                count=random_int(3, 10),
                items=choice(["nodes", "keys", "fragments"]),
                location=choice(self.LOCATIONS).lower(),
                system=choice(["core", "network", "database"]),
                event=choice(["timeout", "lockout", "detection"])
            ),
            "difficulty": difficulty,
            "reward_type": choice(["data", "access", "capability", "knowledge"]),
            "time_limit": random_int(30, 300)
        }
        
        return challenge
    
    def generate_rule(self, trigger_condition: str) -> GameRule:
        """Generate a dynamic game rule."""
        actions = [
            "spawn_defense",
            "increase_difficulty",
            "reveal_hidden_content",
            "trigger_event",
            "adapt_ai"
        ]
        
        return GameRule(
            rule_id=hashlib.sha256(f"{trigger_condition}:{time.time()}".encode()).hexdigest()[:12],
            condition=trigger_condition,
            action=choice(actions),
            priority=random_int(1, 100)
        )


class SelfBuildingEngine:
    """Main self-building game engine."""
    
    def __init__(self, spine_path: Optional[Path] = None):
        self.spine_path = spine_path or Path("self_building_spine.jsonl")
        self.content_gen = ProceduralContentGenerator()
        self.cognition = CognitiveWheel("game_master")
        self.lobbies: Dict[str, Lobby] = {}
        self.build_history: List[BuildEvent] = []
        self.active_rules: List[GameRule] = []
        self.player_behavior: Dict[str, Any] = {
            "actions": [],
            "preferences": {},
            "skill_level": 0.5
        }
        self.build_queue: List[Tuple[BuildTrigger, Dict[str, Any]]] = []
        self.rng = QuantumRNG()
    
    def initialize(self) -> None:
        """Initialize the self-building game."""
        # Create initial lobby
        self._create_initial_lobby()
        
        # Log initialization
        self._log_build(BuildTrigger.TIME_BASED, BuildType.SYSTEM_ENHANCEMENT,
                       "Self-building game initialized")
    
    def _create_initial_lobby(self) -> Lobby:
        """Create the initial game lobby."""
        lobby = Lobby(
            lobby_id="lobby_001",
            lobby_type="entry",
            difficulty=0.3
        )
        
        # Add initial rules
        lobby.add_rule(self.content_gen.generate_rule("threat_level > 0.7"))
        lobby.add_rule(self.content_gen.generate_rule("player_skill > 0.8"))
        
        self.lobbies[lobby.lobby_id] = lobby
        
        return lobby
    
    def process_player_action(self, player_id: str, action: Dict[str, Any]) -> List[BuildEvent]:
        """Process player action and potentially trigger builds."""
        builds = []
        
        # Record behavior
        self.player_behavior["actions"].append({
            "player_id": player_id,
            "action": action,
            "timestamp": time.time()
        })
        
        # Update skill estimate
        action_type = action.get("type", "")
        if action_type == "success":
            self.player_behavior["skill_level"] = min(1.0, self.player_behavior["skill_level"] + 0.05)
        elif action_type == "failure":
            self.player_behavior["skill_level"] = max(0.0, self.player_behavior["skill_level"] - 0.02)
        
        # Check for build triggers
        recent_actions = [a for a in self.player_behavior["actions"]
                         if time.time() - a["timestamp"] < 60]
        
        # Trigger: Many actions in short time
        if len(recent_actions) > 20:
            build = self._trigger_build(BuildTrigger.PLAYER_ACTION, {
                "reason": "high_activity",
                "action_count": len(recent_actions)
            })
            builds.append(build)
        
        # Trigger: Skill advancement
        if self.player_behavior["skill_level"] > 0.8:
            build = self._trigger_build(BuildTrigger.COGNITION_ADVANCE, {
                "reason": "skill_threshold",
                "skill_level": self.player_behavior["skill_level"]
            })
            builds.append(build)
        
        return builds
    
    def _trigger_build(self, trigger: BuildTrigger, context: Dict[str, Any]) -> BuildEvent:
        """Trigger a self-building event."""
        # Determine build type based on trigger and context
        if trigger == BuildTrigger.PLAYER_ACTION:
            build_type = choice([BuildType.NEW_CHALLENGE, BuildType.NEW_LOBBY])
        elif trigger == BuildTrigger.COGNITION_ADVANCE:
            build_type = BuildType.NEW_DEFENSE
        elif trigger == BuildTrigger.THREAT_DETECTED:
            build_type = BuildType.NEW_RULE
        else:
            build_type = choice(list(BuildType))
        
        # Generate build description
        description = self._generate_build_description(build_type, context)
        
        # Create build event
        build = BuildEvent(
            build_id="",
            trigger=trigger,
            build_type=build_type,
            description=description,
            timestamp=time.time(),
            metadata=context
        )
        
        self.build_history.append(build)
        
        # Execute build
        self._execute_build(build)
        
        # Log to spine
        self._log_build(trigger, build_type, description)
        
        return build
    
    def _generate_build_description(self, build_type: BuildType, context: Dict[str, Any]) -> str:
        """Generate description for build event."""
        if build_type == BuildType.NEW_LOBBY:
            return f"Generated new lobby: {self.content_gen.generate_lobby_name()}"
        elif build_type == BuildType.NEW_CHALLENGE:
            challenge = self.content_gen.generate_challenge(self.player_behavior["skill_level"])
            return f"Generated challenge: {challenge['description'][:50]}..."
        elif build_type == BuildType.NEW_RULE:
            return f"Added dynamic rule for condition: {context.get('reason', 'unknown')}"
        elif build_type == BuildType.NEW_DEFENSE:
            return f"Deployed adaptive defense layer"
        else:
            return f"System enhancement: {build_type.name}"
    
    def _execute_build(self, build: BuildEvent) -> None:
        """Execute the build action."""
        if build.build_type == BuildType.NEW_LOBBY:
            # Create new lobby
            lobby = Lobby(
                lobby_id=f"lobby_{len(self.lobbies)+1:03d}",
                lobby_type="generated",
                difficulty=self.player_behavior["skill_level"]
            )
            self.lobbies[lobby.lobby_id] = lobby
            
            # Connect to existing lobby
            if self.lobbies:
                parent = choice(list(self.lobbies.values()))
                parent.connections.append(lobby.lobby_id)
                build.parent_build = parent.lobby_id
        
        elif build.build_type == BuildType.NEW_CHALLENGE:
            # Add challenge to random lobby
            if self.lobbies:
                lobby = choice(list(self.lobbies.values()))
                challenge = self.content_gen.generate_challenge()
                lobby.entities[f"challenge_{len(lobby.entities)}"] = challenge
        
        elif build.build_type == BuildType.NEW_RULE:
            # Add new rule
            rule = self.content_gen.generate_rule(f"trigger_{len(self.active_rules)}")
            self.active_rules.append(rule)
            
            # Add to all lobbies
            for lobby in self.lobbies.values():
                lobby.add_rule(rule)
        
        elif build.build_type == BuildType.SYSTEM_ENHANCEMENT:
            # Advance cognition
            self.cognition.process({"build_executed": build.build_type.name})
    
    def _log_build(self, trigger: BuildTrigger, build_type: BuildType, description: str) -> None:
        """Log build event to spine."""
        event = {
            "type": "self_build",
            "trigger": trigger.name,
            "build_type": build_type.name,
            "description": description,
            "timestamp": time.time(),
            "lobby_count": len(self.lobbies),
            "rule_count": len(self.active_rules)
        }
        append_event(self.spine_path, event)
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get current world state."""
        return {
            "lobbies": len(self.lobbies),
            "active_rules": len(self.active_rules),
            "builds_executed": len(self.build_history),
            "player_skill": self.player_behavior["skill_level"],
            "cognition_stage": self.cognition.state.stage.name,
            "lobbies_detail": {
                lid: {
                    "type": l.lobby_type,
                    "difficulty": l.difficulty,
                    "entities": len(l.entities),
                    "rules": len(l.rules),
                    "connections": l.connections
                }
                for lid, l in self.lobbies.items()
            }
        }
    
    def tick(self) -> List[BuildEvent]:
        """Process one game tick."""
        builds = []
        
        # Process build queue
        while self.build_queue:
            trigger, context = self.build_queue.pop(0)
            build = self._trigger_build(trigger, context)
            builds.append(build)
        
        # Random chance for time-based build
        if random_float() < 0.01:  # 1% chance per tick
            build = self._trigger_build(BuildTrigger.TIME_BASED, {
                "reason": "procedural_generation"
            })
            builds.append(build)
        
        # Evaluate active rules
        context = {
            "threat_level": 0.3,  # Would come from threat engine
            "player_skill": self.player_behavior["skill_level"],
            "lobby_count": len(self.lobbies)
        }
        
        for rule in self.active_rules:
            if rule.enabled and rule.evaluate(context):
                rule.activation_count += 1
                build = self._trigger_build(BuildTrigger.SYSTEM_STRESS, {
                    "reason": f"rule_triggered:{rule.rule_id}"
                })
                builds.append(build)
        
        return builds


# Convenience functions
_engine: Optional[SelfBuildingEngine] = None


def initialize(spine_path: Optional[Path] = None) -> SelfBuildingEngine:
    """Initialize global self-building engine."""
    global _engine
    _engine = SelfBuildingEngine(spine_path)
    _engine.initialize()
    return _engine


def get_engine() -> SelfBuildingEngine:
    """Get global self-building engine."""
    if _engine is None:
        return initialize()
    return _engine
