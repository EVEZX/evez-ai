"""
Meta-Interpreter - Higher-Order Meaning Synthesis

Aggregates multiple interpretations, paths, and paradoxes into
unified meta-interpretations. "Gets as many of what could have been
meant into the means of meaning."
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MetaInterpretation:
    """Higher-order interpretation synthesizing multiple lower interpretations"""
    
    def __init__(self, synthesis_type: str, components: List[Dict]):
        self.synthesis_type = synthesis_type
        self.components = components
        self.timestamp = time.time()
        self.confidence = self._calculate_confidence()
        self.ambiguity = self._calculate_ambiguity()
        
    def _calculate_confidence(self) -> float:
        """Calculate confidence based on component agreement"""
        if not self.components:
            return 0.0
        
        # Average confidence of components
        confidences = [c.get("confidence", 0.5) for c in self.components]
        return sum(confidences) / len(confidences)
    
    def _calculate_ambiguity(self) -> float:
        """Calculate ambiguity (higher = more divergent interpretations)"""
        if len(self.components) < 2:
            return 0.0
        
        # Measure divergence in component interpretations
        return 1.0 / len(self.components)  # Simplified
    
    def to_dict(self) -> Dict:
        return {
            "synthesis_type": self.synthesis_type,
            "component_count": len(self.components),
            "confidence": self.confidence,
            "ambiguity": self.ambiguity,
            "timestamp": self.timestamp
        }


class MetaInterpreter:
    """
    Synthesizes multiple interpretations into higher-order meanings.
    
    Key Concepts:
    - Meta-interpretation: meaning about meanings
    - Synthesis across semantic, causal, and path domains
    - Preservation of ambiguity when fundamental
    - Emergence of new meanings from interpretation composition
    """
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "meta_interpretations.jsonl"
        
        self.meta_interpretations: List[MetaInterpretation] = []
        self.synthesis_history = []
        
    def synthesize_semantic_interpretations(self, interpretations: List[Dict]) -> MetaInterpretation:
        """
        Synthesize multiple semantic interpretations into meta-meaning.
        Captures "all possible meanings" in unified form.
        """
        meta = MetaInterpretation("semantic_synthesis", interpretations)
        self.meta_interpretations.append(meta)
        
        self._log_event("semantic_synthesis", {
            "component_count": len(interpretations),
            "confidence": meta.confidence,
            "ambiguity": meta.ambiguity
        })
        
        return meta
    
    def synthesize_causal_paradoxes(self, paradoxes: List[Dict]) -> MetaInterpretation:
        """
        Synthesize causal paradoxes into meta-understanding.
        Recognizes when contradictions are fundamental vs resolvable.
        """
        meta = MetaInterpretation("causal_paradox_synthesis", paradoxes)
        self.meta_interpretations.append(meta)
        
        self._log_event("causal_synthesis", {
            "paradox_count": len(paradoxes),
            "fundamental_ambiguity": meta.ambiguity
        })
        
        return meta
    
    def synthesize_execution_paths(self, paths: List[Dict]) -> MetaInterpretation:
        """
        Synthesize multiple execution paths into optimal procession meta-understanding.
        """
        meta = MetaInterpretation("path_synthesis", paths)
        self.meta_interpretations.append(meta)
        
        self._log_event("path_synthesis", {
            "path_count": len(paths),
            "optimal_convergence": 1.0 - meta.ambiguity
        })
        
        return meta
    
    def create_unified_meta_interpretation(self, semantic: List[Dict], 
                                          causal: List[Dict], 
                                          paths: List[Dict]) -> MetaInterpretation:
        """
        Create unified meta-interpretation across all domains.
        Ultimate synthesis: "all that could have been meant into means of meaning"
        """
        all_components = semantic + causal + paths
        
        meta = MetaInterpretation("unified_synthesis", all_components)
        self.meta_interpretations.append(meta)
        
        self._log_event("unified_synthesis", {
            "total_components": len(all_components),
            "semantic_count": len(semantic),
            "causal_count": len(causal),
            "path_count": len(paths),
            "final_confidence": meta.confidence,
            "preserved_ambiguity": meta.ambiguity
        })
        
        return meta
    
    def extract_emergent_meanings(self, meta_idx: int) -> List[str]:
        """
        Extract emergent meanings that arise from synthesis.
        Meanings that didn't exist in components but emerge from their combination.
        """
        if meta_idx >= len(self.meta_interpretations):
            return []
        
        meta = self.meta_interpretations[meta_idx]
        
        emergent = []
        
        # Simplified emergent meaning extraction
        if meta.synthesis_type == "semantic_synthesis":
            emergent.append(f"Superposition of {len(meta.components)} meanings creates quantum semantic state")
        elif meta.synthesis_type == "causal_paradox_synthesis":
            emergent.append(f"Paradoxes preserved as fundamental ambiguity: {meta.ambiguity:.2f}")
        elif meta.synthesis_type == "path_synthesis":
            emergent.append(f"Optimal procession emerges from parallel exploration")
        elif meta.synthesis_type == "unified_synthesis":
            emergent.append(f"Unified understanding transcends individual domains")
            emergent.append(f"Confidence: {meta.confidence:.2f}, Ambiguity: {meta.ambiguity:.2f}")
        
        return emergent
    
    def resolve_or_preserve_ambiguity(self, meta_idx: int, 
                                     threshold: float = 0.3) -> Tuple[bool, str]:
        """
        Decide whether to resolve ambiguity or preserve it as fundamental.
        Some ambiguities are essential to meaning.
        """
        if meta_idx >= len(self.meta_interpretations):
            return (False, "Invalid index")
        
        meta = self.meta_interpretations[meta_idx]
        
        if meta.ambiguity < threshold:
            # Low ambiguity: can resolve to single interpretation
            return (True, f"Resolvable: ambiguity {meta.ambiguity:.2f} below threshold {threshold}")
        else:
            # High ambiguity: preserve as fundamental
            return (False, f"Fundamental: ambiguity {meta.ambiguity:.2f} is essential to meaning")
    
    def get_interpretation_hierarchy(self) -> Dict[str, Any]:
        """
        Get hierarchical view of interpretations:
        Raw → Interpretations → Meta-interpretations → Emergent meanings
        """
        hierarchy = {
            "total_meta_interpretations": len(self.meta_interpretations),
            "by_type": {},
            "average_confidence": 0.0,
            "average_ambiguity": 0.0
        }
        
        if self.meta_interpretations:
            # Group by type
            for meta in self.meta_interpretations:
                stype = meta.synthesis_type
                if stype not in hierarchy["by_type"]:
                    hierarchy["by_type"][stype] = []
                hierarchy["by_type"][stype].append(meta.to_dict())
            
            # Averages
            hierarchy["average_confidence"] = sum(m.confidence for m in self.meta_interpretations) / len(self.meta_interpretations)
            hierarchy["average_ambiguity"] = sum(m.ambiguity for m in self.meta_interpretations) / len(self.meta_interpretations)
        
        return hierarchy
    
    def generate_meaning_report(self) -> str:
        """
        Generate human-readable report of all interpretations and meanings.
        "What could have been meant" captured and synthesized.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("META-INTERPRETATION REPORT")
        lines.append("=" * 60)
        
        hierarchy = self.get_interpretation_hierarchy()
        
        lines.append(f"\nTotal Meta-Interpretations: {hierarchy['total_meta_interpretations']}")
        lines.append(f"Average Confidence: {hierarchy['average_confidence']:.2f}")
        lines.append(f"Average Ambiguity: {hierarchy['average_ambiguity']:.2f}")
        
        lines.append("\nBy Type:")
        for stype, metas in hierarchy["by_type"].items():
            lines.append(f"  {stype}: {len(metas)} interpretations")
        
        lines.append("\nEmergent Meanings:")
        for i, meta in enumerate(self.meta_interpretations):
            emergent = self.extract_emergent_meanings(i)
            if emergent:
                lines.append(f"  [{i}] {meta.synthesis_type}:")
                for meaning in emergent:
                    lines.append(f"      - {meaning}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _log_event(self, event_type: str, data: Dict):
        """Log meta-interpretation events"""
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


def perform_meta_interpretation(semantic_data: List[Dict], 
                               causal_data: List[Dict], 
                               path_data: List[Dict]) -> Dict[str, Any]:
    """
    Main entry point: Perform complete meta-interpretation synthesis
    """
    interpreter = MetaInterpreter()
    
    # Individual syntheses
    semantic_meta = interpreter.synthesize_semantic_interpretations(semantic_data)
    causal_meta = interpreter.synthesize_causal_paradoxes(causal_data)
    path_meta = interpreter.synthesize_execution_paths(path_data)
    
    # Unified synthesis
    unified = interpreter.create_unified_meta_interpretation(
        semantic_data, causal_data, path_data
    )
    
    # Extract emergent meanings
    emergent = interpreter.extract_emergent_meanings(len(interpreter.meta_interpretations) - 1)
    
    # Decision on ambiguity
    should_resolve, reason = interpreter.resolve_or_preserve_ambiguity(
        len(interpreter.meta_interpretations) - 1
    )
    
    # Generate report
    report = interpreter.generate_meaning_report()
    
    return {
        "semantic_meta": semantic_meta.to_dict(),
        "causal_meta": causal_meta.to_dict(),
        "path_meta": path_meta.to_dict(),
        "unified_meta": unified.to_dict(),
        "emergent_meanings": emergent,
        "ambiguity_resolution": {
            "should_resolve": should_resolve,
            "reason": reason
        },
        "hierarchy": interpreter.get_interpretation_hierarchy(),
        "report": report
    }


if __name__ == "__main__":
    # Test
    result = perform_meta_interpretation(
        semantic_data=[{"content": "literal", "confidence": 0.8}, {"content": "metaphorical", "confidence": 0.7}],
        causal_data=[{"violation": "temporal", "type": "paradox"}],
        path_data=[{"path_id": "A", "score": 0.9}, {"path_id": "B", "score": 0.7}]
    )
    
    print(result["report"])
    print(f"\nEmergent Meanings: {len(result['emergent_meanings'])}")
    print(f"Ambiguity Decision: {result['ambiguity_resolution']['reason']}")
