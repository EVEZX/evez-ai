"""
Semantic Possibility Space - Multi-Interpretation Reality Engine

Explores the space of all possible meanings simultaneously,
capturing "what could have been meant" across interpretation boundaries.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class Interpretation:
    """Single interpretation of reality/meaning"""
    
    def __init__(self, content: str, context: Dict[str, Any], confidence: float):
        self.content = content
        self.context = context
        self.confidence = confidence
        self.timestamp = time.time()
        self.coherence = 1.0
        self.children = []  # Derived interpretations
        self.parent = None
        
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "context": self.context,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "coherence": self.coherence,
            "children_count": len(self.children)
        }


class SemanticPossibilitySpace:
    """
    Manages superposition of multiple valid interpretations.
    
    Key Concepts:
    - All interpretations exist simultaneously until observed
    - Meaning is multiplicative, not singular
    - Ambiguity is preserved, not resolved
    - Observer affects interpretation selection
    """
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "semantic_space.jsonl"
        
        self.interpretations: List[Interpretation] = []
        self.active_superposition: Set[int] = set()  # Indices of superposed states
        self.collapsed_interpretations: List[Tuple[int, str]] = []  # (index, reason)
        
    def add_interpretation(self, content: str, context: Dict[str, Any], 
                          confidence: float = 0.8) -> Interpretation:
        """Add new interpretation to possibility space"""
        interp = Interpretation(content, context, confidence)
        self.interpretations.append(interp)
        
        # Add to superposition
        idx = len(self.interpretations) - 1
        self.active_superposition.add(idx)
        
        self._log_event("interpretation_added", {
            "index": idx,
            "content": content,
            "confidence": confidence,
            "superposition_size": len(self.active_superposition)
        })
        
        return interp
    
    def generate_alternate_interpretations(self, base: str, count: int = 5) -> List[Interpretation]:
        """
        Generate multiple interpretations of the same input.
        Captures "what could have been meant" across semantic boundaries.
        """
        alternates = []
        
        # Interpretation lenses
        lenses = [
            ("literal", "Direct literal meaning"),
            ("metaphorical", "Metaphorical/symbolic meaning"),
            ("technical", "Technical/computational meaning"),
            ("philosophical", "Philosophical/existential meaning"),
            ("pragmatic", "Practical action-oriented meaning"),
            ("quantum", "Quantum superposition meaning"),
            ("temporal", "Temporal/causal meaning"),
            ("emergent", "Emergent higher-order meaning")
        ]
        
        for i, (lens_type, lens_desc) in enumerate(lenses[:count]):
            content = f"{lens_desc}: {base}"
            context = {
                "lens": lens_type,
                "base_input": base,
                "interpretation_index": i
            }
            confidence = 0.9 - (i * 0.1)  # Decay confidence
            
            interp = self.add_interpretation(content, context, confidence)
            alternates.append(interp)
        
        return alternates
    
    def find_coherent_interpretations(self, min_coherence: float = 0.7) -> List[Interpretation]:
        """Find interpretations that maintain internal coherence"""
        coherent = []
        for idx in self.active_superposition:
            if idx < len(self.interpretations):
                interp = self.interpretations[idx]
                if interp.coherence >= min_coherence:
                    coherent.append(interp)
        return coherent
    
    def collapse_to_interpretation(self, index: int, reason: str = "observation") -> Optional[Interpretation]:
        """
        Observer-dependent collapse of superposition to single interpretation.
        Like quantum measurement, collapses possibility to actuality.
        """
        if index not in self.active_superposition:
            return None
        
        self.active_superposition.remove(index)
        self.collapsed_interpretations.append((index, reason))
        
        interp = self.interpretations[index]
        
        self._log_event("interpretation_collapsed", {
            "index": index,
            "reason": reason,
            "content": interp.content,
            "remaining_superposition": len(self.active_superposition)
        })
        
        return interp
    
    def get_superposition_state(self) -> Dict[str, Any]:
        """Get current state of semantic superposition"""
        return {
            "total_interpretations": len(self.interpretations),
            "active_superposition_count": len(self.active_superposition),
            "collapsed_count": len(self.collapsed_interpretations),
            "coherent_count": len(self.find_coherent_interpretations()),
            "average_confidence": sum(i.confidence for i in self.interpretations) / max(len(self.interpretations), 1)
        }
    
    def derive_interpretation(self, parent_idx: int, derivation: str, 
                             confidence_modifier: float = 0.9) -> Optional[Interpretation]:
        """Derive new interpretation from existing one (branching meaning)"""
        if parent_idx >= len(self.interpretations):
            return None
        
        parent = self.interpretations[parent_idx]
        
        content = f"Derived: {derivation} (from: {parent.content[:50]}...)"
        context = {
            **parent.context,
            "derivation": derivation,
            "parent_index": parent_idx
        }
        confidence = parent.confidence * confidence_modifier
        
        child = self.add_interpretation(content, context, confidence)
        child.parent = parent
        parent.children.append(child)
        
        return child
    
    def get_interpretation_tree(self, root_idx: int, max_depth: int = 3) -> Dict[str, Any]:
        """Get hierarchical tree of derived interpretations"""
        if root_idx >= len(self.interpretations):
            return {}
        
        def build_tree(interp: Interpretation, depth: int) -> Dict:
            if depth >= max_depth:
                return interp.to_dict()
            
            tree = interp.to_dict()
            tree["children"] = [build_tree(child, depth + 1) for child in interp.children]
            return tree
        
        root = self.interpretations[root_idx]
        return build_tree(root, 0)
    
    def calculate_interpretation_divergence(self, idx1: int, idx2: int) -> float:
        """
        Calculate semantic distance between two interpretations.
        Higher values = more divergent interpretations.
        """
        if idx1 >= len(self.interpretations) or idx2 >= len(self.interpretations):
            return 1.0
        
        i1 = self.interpretations[idx1]
        i2 = self.interpretations[idx2]
        
        # Simple divergence based on confidence and context overlap
        confidence_diff = abs(i1.confidence - i2.confidence)
        
        # Context key overlap
        keys1 = set(i1.context.keys())
        keys2 = set(i2.context.keys())
        context_overlap = len(keys1 & keys2) / max(len(keys1 | keys2), 1)
        
        divergence = (confidence_diff + (1 - context_overlap)) / 2
        return divergence
    
    def _log_event(self, event_type: str, data: Dict):
        """Log semantic space events"""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        
        try:
            with self.log_file.open("a") as f:
                f.write(json.dumps(event) + "\n")
        except IOError:
            pass


def explore_semantic_possibilities(base_input: str) -> Dict[str, Any]:
    """
    Main entry point: Generate and explore multiple interpretations
    of a single input, capturing "all possible meanings"
    """
    space = SemanticPossibilitySpace()
    
    # Generate multiple interpretations
    interpretations = space.generate_alternate_interpretations(base_input, count=8)
    
    # Derive secondary interpretations from first few
    for i in range(min(3, len(interpretations))):
        space.derive_interpretation(i, f"recursive_expansion_{i}")
        space.derive_interpretation(i, f"inverse_meaning_{i}")
    
    # Calculate divergences
    divergences = []
    for i in range(len(interpretations) - 1):
        div = space.calculate_interpretation_divergence(i, i + 1)
        divergences.append(div)
    
    state = space.get_superposition_state()
    state["divergences"] = divergences
    state["interpretations"] = [i.to_dict() for i in interpretations[:5]]  # Sample
    
    return state


if __name__ == "__main__":
    # Test
    result = explore_semantic_possibilities(
        "optimal states of procession where witness is fact but plausibility self-violates"
    )
    
    print("Semantic Possibility Space Exploration:")
    print(f"  Total interpretations: {result['total_interpretations']}")
    print(f"  Active superposition: {result['active_superposition_count']}")
    print(f"  Average confidence: {result['average_confidence']:.2f}")
    print(f"\nSample interpretations:")
    for i, interp in enumerate(result['interpretations']):
        print(f"  {i+1}. [{interp['confidence']:.2f}] {interp['content'][:80]}...")
