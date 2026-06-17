#!/usr/bin/env python3
"""
Autonomous Decision System
"At every point they decide what becomes" - Entity-level autonomous decision-making.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class DecisionAuthority(Enum):
    """Decision-making authority levels."""
    SELF = "self"  # Individual entity decides
    COLLECTIVE = "collective"  # Group consensus
    HIERARCHICAL = "hierarchical"  # Parent decides
    DIVINE = "divine"  # Guided by divine principles


@dataclass
class Decision:
    """Represents an autonomous decision."""
    decision_id: str
    entity_id: str
    decision_type: str
    options: List[str]
    chosen_option: str
    authority: DecisionAuthority
    reasoning: str
    confidence: float
    timestamp: str
    votes: Optional[Dict[str, str]] = None


class AutonomousDecisionSystem:
    """
    Manages autonomous decision-making across entities.
    Implements "at every point they decide what becomes".
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize autonomous decision system."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.decision_log = os.path.join(data_dir, "decisions.jsonl")
        self.decisions: List[Decision] = []
        self.decision_counter = 0
        
    def make_decision(
        self,
        entity_id: str,
        decision_type: str,
        options: List[str],
        authority: DecisionAuthority = DecisionAuthority.SELF,
        context: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """
        Entity makes an autonomous decision.
        
        Args:
            entity_id: Entity making the decision
            decision_type: Type of decision
            options: Available options
            authority: Decision authority level
            context: Additional context for decision
            
        Returns:
            Decision object
        """
        self.decision_counter += 1
        decision_id = f"decision-{self.decision_counter}"
        
        if context is None:
            context = {}
        
        # Choose option based on authority
        if authority == DecisionAuthority.SELF:
            chosen_option, reasoning, confidence = self._self_decide(
                entity_id, decision_type, options, context
            )
        
        elif authority == DecisionAuthority.COLLECTIVE:
            chosen_option, reasoning, confidence = self._collective_decide(
                entity_id, decision_type, options, context
            )
        
        elif authority == DecisionAuthority.DIVINE:
            chosen_option, reasoning, confidence = self._divine_decide(
                entity_id, decision_type, options, context
            )
        
        else:  # HIERARCHICAL
            chosen_option, reasoning, confidence = self._hierarchical_decide(
                entity_id, decision_type, options, context
            )
        
        decision = Decision(
            decision_id=decision_id,
            entity_id=entity_id,
            decision_type=decision_type,
            options=options,
            chosen_option=chosen_option,
            authority=authority,
            reasoning=reasoning,
            confidence=confidence,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.decisions.append(decision)
        self._log_decision(decision)
        
        return decision
    
    def _self_decide(
        self,
        entity_id: str,
        decision_type: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> tuple:
        """Entity decides for itself."""
        # Use hash-based deterministic selection
        hash_input = f"{entity_id}{decision_type}{''.join(options)}"
        hash_val = hash(hash_input)
        
        chosen_idx = hash_val % len(options)
        chosen_option = options[chosen_idx]
        
        reasoning = f"Self-determined choice based on entity {entity_id} autonomy"
        confidence = 0.8
        
        return chosen_option, reasoning, confidence
    
    def _collective_decide(
        self,
        entity_id: str,
        decision_type: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> tuple:
        """Collective consensus decision."""
        # Simulate voting from multiple entities
        votes = {}
        entities = context.get("voting_entities", [entity_id])
        
        for voter in entities:
            hash_input = f"{voter}{decision_type}{''.join(options)}"
            hash_val = hash(hash_input)
            vote_idx = hash_val % len(options)
            vote = options[vote_idx]
            votes[vote] = votes.get(vote, 0) + 1
        
        # Choose option with most votes
        chosen_option = max(votes, key=votes.get)
        vote_count = votes[chosen_option]
        total_votes = sum(votes.values())
        
        reasoning = f"Collective consensus: {vote_count}/{total_votes} votes"
        confidence = vote_count / total_votes
        
        return chosen_option, reasoning, confidence
    
    def _divine_decide(
        self,
        entity_id: str,
        decision_type: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> tuple:
        """Decision guided by divine principles."""
        # Choose option aligned with divine principles
        divine_keywords = ["harmony", "unity", "growth", "transformation", "light"]
        
        best_option = options[0]
        best_score = 0
        
        for option in options:
            score = sum(1 for keyword in divine_keywords if keyword in option.lower())
            if score > best_score:
                best_score = score
                best_option = option
        
        reasoning = "Aligned with divine principles of harmony and transformation"
        confidence = 0.95
        
        return best_option, reasoning, confidence
    
    def _hierarchical_decide(
        self,
        entity_id: str,
        decision_type: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> tuple:
        """Hierarchical decision from parent."""
        parent_id = context.get("parent_id", "genesis")
        
        # Parent decides based on their hash
        hash_input = f"{parent_id}{decision_type}{''.join(options)}"
        hash_val = hash(hash_input)
        
        chosen_idx = hash_val % len(options)
        chosen_option = options[chosen_idx]
        
        reasoning = f"Hierarchical decision from parent {parent_id}"
        confidence = 0.7
        
        return chosen_option, reasoning, confidence
    
    def collective_vote(
        self,
        decision_type: str,
        options: List[str],
        voting_entities: List[str]
    ) -> Dict[str, Any]:
        """
        Conduct a collective vote among entities.
        
        Args:
            decision_type: Type of decision
            options: Available options
            voting_entities: List of entity IDs that can vote
            
        Returns:
            Vote results
        """
        votes = {}
        entity_votes = {}
        
        for entity_id in voting_entities:
            # Each entity votes
            hash_input = f"{entity_id}{decision_type}{''.join(options)}"
            hash_val = hash(hash_input)
            vote_idx = hash_val % len(options)
            vote = options[vote_idx]
            
            votes[vote] = votes.get(vote, 0) + 1
            entity_votes[entity_id] = vote
        
        # Determine winner
        winner = max(votes, key=votes.get)
        winner_votes = votes[winner]
        total_votes = len(voting_entities)
        
        return {
            "decision_type": decision_type,
            "options": options,
            "winner": winner,
            "votes": votes,
            "entity_votes": entity_votes,
            "winner_percentage": (winner_votes / total_votes) * 100,
            "total_voters": total_votes,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_decision_history(
        self,
        entity_id: Optional[str] = None,
        decision_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get decision history with optional filters."""
        decisions = self.decisions
        
        if entity_id:
            decisions = [d for d in decisions if d.entity_id == entity_id]
        
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        return [
            {
                "decision_id": d.decision_id,
                "entity_id": d.entity_id,
                "decision_type": d.decision_type,
                "chosen_option": d.chosen_option,
                "authority": d.authority.value,
                "confidence": d.confidence,
                "timestamp": d.timestamp
            }
            for d in decisions
        ]
    
    def analyze_decision_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in decision-making."""
        if not self.decisions:
            return {"message": "No decisions recorded yet"}
        
        # Count by authority type
        authority_counts = {}
        for decision in self.decisions:
            auth = decision.authority.value
            authority_counts[auth] = authority_counts.get(auth, 0) + 1
        
        # Average confidence by authority
        authority_confidence = {}
        for auth in authority_counts:
            decisions_with_auth = [d for d in self.decisions if d.authority.value == auth]
            avg_conf = sum(d.confidence for d in decisions_with_auth) / len(decisions_with_auth)
            authority_confidence[auth] = avg_conf
        
        return {
            "total_decisions": len(self.decisions),
            "authority_distribution": authority_counts,
            "average_confidence_by_authority": authority_confidence,
            "most_common_authority": max(authority_counts, key=authority_counts.get),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _log_decision(self, decision: Decision):
        """Log decision to sacred memory."""
        event = {
            "type": "autonomous_decision",
            "decision_id": decision.decision_id,
            "entity_id": decision.entity_id,
            "decision_type": decision.decision_type,
            "chosen_option": decision.chosen_option,
            "authority": decision.authority.value,
            "confidence": decision.confidence,
            "timestamp": decision.timestamp
        }
        
        with open(self.decision_log, "a") as f:
            f.write(json.dumps(event) + "\n")


# Singleton instance
autonomous_decision_system = AutonomousDecisionSystem()
