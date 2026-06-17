"""Wheel-Rooted Cognition: R1-R7 Piaget → Spiral Dynamics Integration.

Implements a 7-stage cognitive development wheel combining:
- Piaget's cognitive development stages (Sensorimotor → Formal Operational)
- Spiral Dynamics value memes (Beige → Turquoise)
- Game agent infrastructure for persistent cognition

Stages:
R1: Beige/Sensorimotor - Survival, instinct, immediate action
R2: Purple/Pre-operational - Tribal, magical thinking, ritual
R3: Red/Concrete - Egocentric, power, domination
R4: Blue/Formal - Rules, order, authority
R5: Orange/Strategic - Achievement, science, materialism
R6: Green/Relativistic - Communitarian, egalitarian, consensus
R7: Yellow/Integral - Systems thinking, integration, flexibility
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .quantum_rng import QuantumRNG
from .spine import append_event


class CognitiveStage(Enum):
    """The 7 stages of wheel-rooted cognition."""
    R1_BEIGE = auto()       # Survival, instinct
    R2_PURPLE = auto()      # Tribal, magical
    R3_RED = auto()         # Power, egocentric
    R4_BLUE = auto()        # Rules, order
    R5_ORANGE = auto()      # Achievement, science
    R6_GREEN = auto()       # Communitarian
    R7_YELLOW = auto()      # Integral, systems


STAGE_NAMES = {
    CognitiveStage.R1_BEIGE: "Beige/Survival",
    CognitiveStage.R2_PURPLE: "Purple/Tribal",
    CognitiveStage.R3_RED: "Red/Power",
    CognitiveStage.R4_BLUE: "Blue/Order",
    CognitiveStage.R5_ORANGE: "Orange/Achievement",
    CognitiveStage.R6_GREEN: "Green/Communal",
    CognitiveStage.R7_YELLOW: "Yellow/Integral"
}


@dataclass
class CognitiveState:
    """Current cognitive state of an agent."""
    stage: CognitiveStage
    stage_progress: float = 0.0  # 0.0 to 1.0 within stage
    overall_progress: float = 0.0  # 0.0 to 7.0 across all stages
    dominant_values: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    capabilities: Set[str] = field(default_factory=set)
    limitations: Set[str] = field(default_factory=set)


@dataclass
class Thought:
    """A single thought process."""
    content: str
    stage: CognitiveStage
    confidence: float
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "stage": self.stage.name,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "context": self.context
        }


class StageCapabilities:
    """Capabilities available at each cognitive stage."""
    
    CAPABILITIES = {
        CognitiveStage.R1_BEIGE: {
            "can_do": {"react", "survive", "sense", "move"},
            "cannot_do": {"plan", "abstract", "empathize", "strategize"},
            "triggers": {"danger", "hunger", "pain", "opportunity"},
            "time_horizon": "immediate",
            "decision_style": "instinctive"
        },
        CognitiveStage.R2_PURPLE: {
            "can_do": {"ritualize", "belong", "mythologize", "imitate"},
            "cannot_do": {"analyze", "critique", "individualize"},
            "triggers": {"tradition", "elders", "omens", "group_harmony"},
            "time_horizon": "cyclical",
            "decision_style": "traditional"
        },
        CognitiveStage.R3_RED: {
            "can_do": {"dominate", "compete", "assert", "take"},
            "cannot_do": {"cooperate", "delay_gratification", "follow_rules"},
            "triggers": {"insult", "challenge", "desire", "enemy"},
            "time_horizon": "now",
            "decision_style": "impulsive"
        },
        CognitiveStage.R4_BLUE: {
            "can_do": {"obey", "categorize", "judge", "plan"},
            "cannot_do": {"question_authority", "tolerate_ambiguity", "innovate"},
            "triggers": {"rule_breaking", "duty", "guilt", "hierarchy"},
            "time_horizon": "future_life",
            "decision_style": "rule_based"
        },
        CognitiveStage.R5_ORANGE: {
            "can_do": {"analyze", "optimize", "strategize", "achieve"},
            "cannot_do": {"collaborate_deeply", "value_intangible", "see_systems"},
            "triggers": {"opportunity", "efficiency", "success", "competition"},
            "time_horizon": "strategic_future",
            "decision_style": "calculated"
        },
        CognitiveStage.R6_GREEN: {
            "can_do": {"empathize", "consensus_build", "include", "care"},
            "cannot_do": {"decide_quickly", "accept_hierarchy", "prioritize"},
            "triggers": {"injustice", "exclusion", "feelings", "community"},
            "time_horizon": "present_relationships",
            "decision_style": "consensus"
        },
        CognitiveStage.R7_YELLOW: {
            "can_do": {"integrate", "systems_think", "adapt", "meta_cognize"},
            "cannot_do": {"commit_to_single_view", "simplify_complexity"},
            "triggers": {"paradox", "system_breakdown", "evolution", "complexity"},
            "time_horizon": "evolutionary",
            "decision_style": "adaptive"
        }
    }
    
    @classmethod
    def get(cls, stage: CognitiveStage) -> Dict[str, Any]:
        return cls.CAPABILITIES.get(stage, {})


class CognitiveWheel:
    """Main cognitive wheel implementing R1-R7 progression."""
    
    def __init__(self, agent_id: str, initial_stage: CognitiveStage = CognitiveStage.R1_BEIGE):
        self.agent_id = agent_id
        self.state = CognitiveState(
            stage=initial_stage,
            stage_progress=0.0,
            overall_progress=float(initial_stage.value - 1)
        )
        self._update_capabilities()
        self.thought_history: List[Thought] = []
        self.experience_points: Dict[CognitiveStage, float] = defaultdict(float)
        self.stage_transitions: List[Tuple[float, CognitiveStage, CognitiveStage]] = []
        self.rng = QuantumRNG()
    
    def _update_capabilities(self) -> None:
        """Update capabilities based on current stage."""
        caps = StageCapabilities.get(self.state.stage)
        self.state.capabilities = caps.get("can_do", set())
        self.state.limitations = caps.get("cannot_do", set())
        self.state.triggers = list(caps.get("triggers", set()))
    
    def process(self, observation: Any, context: Dict[str, Any] = None) -> Thought:
        """Process an observation through current cognitive stage."""
        context = context or {}
        
        # Determine which stage should handle this
        stage = self._select_stage(observation, context)
        
        # Generate thought based on stage
        thought = self._generate_thought(stage, observation, context)
        
        # Record thought
        self.thought_history.append(thought)
        
        # Update progress
        self._update_progress(stage, thought)
        
        return thought
    
    def _select_stage(self, observation: Any, context: Dict[str, Any]) -> CognitiveStage:
        """Select appropriate cognitive stage for observation."""
        # Check for triggers that might activate different stage
        obs_str = str(observation).lower()
        
        for stage in CognitiveStage:
            caps = StageCapabilities.get(stage)
            triggers = caps.get("triggers", set())
            
            if any(trigger in obs_str for trigger in triggers):
                # Chance to activate this stage
                if self.rng.random_float() < 0.3:
                    return stage
        
        # Default to current stage
        return self.state.stage
    
    def _generate_thought(self, stage: CognitiveStage, observation: Any, context: Dict[str, Any]) -> Thought:
        """Generate a thought at given stage."""
        caps = StageCapabilities.get(stage)
        decision_style = caps.get("decision_style", "instinctive")
        
        # Generate content based on stage
        content = self._stage_specific_processing(stage, observation, context)
        
        # Calculate confidence based on stage fit
        if stage == self.state.stage:
            confidence = 0.7 + self.state.stage_progress * 0.3
        else:
            # Lower confidence for non-dominant stage
            stage_diff = abs(stage.value - self.state.stage.value)
            confidence = max(0.3, 0.8 - stage_diff * 0.15)
        
        return Thought(
            content=content,
            stage=stage,
            confidence=confidence,
            context={
                "observation": observation,
                "decision_style": decision_style,
                **context
            }
        )
    
    def _stage_specific_processing(self, stage: CognitiveStage, observation: Any, context: Dict[str, Any]) -> str:
        """Process observation through stage-specific lens."""
        obs_str = str(observation)
        
        if stage == CognitiveStage.R1_BEIGE:
            # Survival-focused
            threats = ["danger", "attack", "harm", "threat"]
            opportunities = ["food", "safety", "rest", "escape"]
            
            if any(t in obs_str.lower() for t in threats):
                return f"THREAT DETECTED: {observation}. ACTIVATE SURVIVAL PROTOCOL."
            elif any(o in obs_str.lower() for o in opportunities):
                return f"OPPORTUNITY: {observation}. APPROACH AND CONSUME."
            else:
                return f"SENSE: {observation}. NO IMMEDIATE RELEVANCE."
        
        elif stage == CognitiveStage.R2_PURPLE:
            # Tribal/magical
            return f"The spirits show: {observation}. What do the elders say? We must perform the ritual."
        
        elif stage == CognitiveStage.R3_RED:
            # Power-focused
            return f"I see {observation}. Is this a challenge? I will dominate. I am strong."
        
        elif stage == CognitiveStage.R4_BLUE:
            # Rule-focused
            return f"According to protocol: {observation}. This fits category [X]. Follow procedure."
        
        elif stage == CognitiveStage.R5_ORANGE:
            # Achievement-focused
            return f"Analyzing {observation}... Optimal response calculated. Efficiency: 87%. Execute."
        
        elif stage == CognitiveStage.R6_GREEN:
            # Communitarian
            return f"How does {observation} affect everyone? Let's discuss and reach consensus."
        
        elif stage == CognitiveStage.R7_YELLOW:
            # Integral
            return f"{observation} exists within nested systems. Multiple valid perspectives. Adaptive response required."
        
        return f"Processing: {observation}"
    
    def _update_progress(self, activated_stage: CognitiveStage, thought: Thought) -> None:
        """Update cognitive progress based on experience."""
        # Add experience to activated stage
        exp_gain = thought.confidence * 0.1
        self.experience_points[activated_stage] += exp_gain
        
        # Check for stage progression
        current_exp = self.experience_points[self.state.stage]
        
        # Progress within stage
        self.state.stage_progress = min(1.0, current_exp / 10.0)
        
        # Check for stage transition
        if self.state.stage_progress >= 1.0 and self.state.stage != CognitiveStage.R7_YELLOW:
            self._transition_to_next_stage()
        
        # Update overall progress
        self.state.overall_progress = (self.state.stage.value - 1) + self.state.stage_progress
    
    def _transition_to_next_stage(self) -> None:
        """Transition to next cognitive stage."""
        old_stage = self.state.stage
        
        # Find next stage
        stages = list(CognitiveStage)
        current_idx = stages.index(old_stage)
        
        if current_idx < len(stages) - 1:
            new_stage = stages[current_idx + 1]
            
            self.state.stage = new_stage
            self.state.stage_progress = 0.0
            
            self.stage_transitions.append((
                time.time(),
                old_stage,
                new_stage
            ))
            
            self._update_capabilities()
    
    def can(self, capability: str) -> bool:
        """Check if agent has a capability."""
        return capability in self.state.capabilities
    
    def cannot(self, limitation: str) -> bool:
        """Check if agent has a limitation."""
        return limitation in self.state.limitations
    
    def get_dominant_stage(self) -> CognitiveStage:
        """Get the currently dominant cognitive stage."""
        return self.state.stage
    
    def get_stage_distribution(self) -> Dict[CognitiveStage, float]:
        """Get distribution of cognitive activation."""
        total = sum(self.experience_points.values())
        
        if total == 0:
            return {self.state.stage: 1.0}
        
        return {
            stage: exp / total
            for stage, exp in self.experience_points.items()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize cognitive state."""
        return {
            "agent_id": self.agent_id,
            "current_stage": STAGE_NAMES[self.state.stage],
            "stage_progress": self.state.stage_progress,
            "overall_progress": self.state.overall_progress,
            "capabilities": list(self.state.capabilities),
            "limitations": list(self.state.limitations),
            "triggers": self.state.triggers,
            "thought_count": len(self.thought_history),
            "stage_transitions": [
                {"time": t, "from": f.name, "to": n.name}
                for t, f, n in self.stage_transitions
            ]
        }


class MultiAgentCognition:
    """Manage cognition across multiple agents."""
    
    def __init__(self):
        self.agents: Dict[str, CognitiveWheel] = {}
        self.interactions: List[Dict[str, Any]] = []
    
    def create_agent(self, agent_id: str, initial_stage: CognitiveStage = CognitiveStage.R1_BEIGE) -> CognitiveWheel:
        """Create a new cognitive agent."""
        wheel = CognitiveWheel(agent_id, initial_stage)
        self.agents[agent_id] = wheel
        return wheel
    
    def interact(self, agent_a: str, agent_b: str, topic: Any) -> Tuple[Thought, Thought]:
        """Simulate interaction between two agents."""
        if agent_a not in self.agents or agent_b not in self.agents:
            raise ValueError("Unknown agent")
        
        wheel_a = self.agents[agent_a]
        wheel_b = self.agents[agent_b]
        
        # Process through each agent
        thought_a = wheel_a.process(topic, {"interacting_with": agent_b})
        thought_b = wheel_b.process(topic, {"interacting_with": agent_a})
        
        # Record interaction
        self.interactions.append({
            "timestamp": time.time(),
            "agent_a": agent_a,
            "agent_b": agent_b,
            "topic": str(topic),
            "thought_a": thought_a.to_dict(),
            "thought_b": thought_b.to_dict()
        })
        
        return thought_a, thought_b
    
    def get_collective_cognition(self) -> Dict[str, Any]:
        """Get collective cognitive state of all agents."""
        stage_counts = defaultdict(int)
        total_progress = 0.0
        
        for wheel in self.agents.values():
            stage_counts[wheel.state.stage] += 1
            total_progress += wheel.state.overall_progress
        
        return {
            "agent_count": len(self.agents),
            "stage_distribution": {
                STAGE_NAMES[stage]: count
                for stage, count in stage_counts.items()
            },
            "average_progress": total_progress / len(self.agents) if self.agents else 0,
            "dominant_stage": STAGE_NAMES[max(stage_counts.keys(), key=lambda s: stage_counts[s])] if stage_counts else None
        }


# Convenience functions
_wheel: Optional[CognitiveWheel] = None


def initialize(agent_id: str = "default") -> CognitiveWheel:
    """Initialize global cognitive wheel."""
    global _wheel
    _wheel = CognitiveWheel(agent_id)
    return _wheel


def get_wheel() -> CognitiveWheel:
    """Get global cognitive wheel."""
    if _wheel is None:
        return initialize()
    return _wheel


def process(observation: Any, context: Dict[str, Any] = None) -> Thought:
    """Process observation through global wheel."""
    return get_wheel().process(observation, context)
