"""
Multi-Path Optimizer - Parallel State Exploration & Optimal Procession Selection

Explores "optimal states of procession" by maintaining and evaluating
multiple parallel execution paths simultaneously.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ExecutionPath:
    """Single path through state space"""
    
    def __init__(self, path_id: str, initial_state: Dict[str, Any]):
        self.path_id = path_id
        self.states = [initial_state]
        self.score = 0.0
        self.coherence = 1.0
        self.timestamp = time.time()
        self.is_optimal = False
        
    def add_state(self, state: Dict[str, Any]):
        """Add state to path"""
        self.states.append(state)
        
    def calculate_score(self) -> float:
        """Calculate path quality score"""
        # Factors: length, coherence, final state value
        length_score = len(self.states) / 100  # Normalize
        
        # Final state value
        final_value = self.states[-1].get("value", 0.0) if self.states else 0.0
        
        # Coherence penalty
        coherence_factor = self.coherence
        
        self.score = (length_score * 0.3 + final_value * 0.5 + coherence_factor * 0.2)
        return self.score
    
    def to_dict(self) -> Dict:
        return {
            "path_id": self.path_id,
            "states_count": len(self.states),
            "score": self.score,
            "coherence": self.coherence,
            "is_optimal": self.is_optimal,
            "timestamp": self.timestamp
        }


class MultiPathOptimizer:
    """
    Manages parallel exploration of multiple execution paths.
    
    Key Concepts:
    - All paths explored simultaneously (parallel procession)
    - Optimal selection based on multi-dimensional criteria
    - Path branching at decision points
    - Coherence tracking across paths
    """
    
    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "multi_path.jsonl"
        
        self.paths: List[ExecutionPath] = []
        self.decision_points = []
        self.optimal_paths = []
        
    def initialize_path(self, path_id: str, initial_state: Dict[str, Any]) -> ExecutionPath:
        """Initialize new execution path"""
        path = ExecutionPath(path_id, initial_state)
        self.paths.append(path)
        
        self._log_event("path_initialized", {
            "path_id": path_id,
            "initial_state": initial_state,
            "total_paths": len(self.paths)
        })
        
        return path
    
    def branch_path(self, parent_idx: int, branch_id: str, 
                   branch_state: Dict[str, Any]) -> Optional[ExecutionPath]:
        """
        Create branch from existing path at decision point.
        Enables exploration of alternate processions.
        """
        if parent_idx >= len(self.paths):
            return None
        
        parent = self.paths[parent_idx]
        
        # Create child path with parent's history
        child_id = f"{parent.path_id}-{branch_id}"
        child = ExecutionPath(child_id, parent.states[0])
        
        # Copy parent states
        for state in parent.states[1:]:
            child.add_state(state)
        
        # Add branch state
        child.add_state(branch_state)
        child.coherence = parent.coherence * 0.9  # Branching reduces coherence
        
        self.paths.append(child)
        
        self._log_event("path_branched", {
            "parent_id": parent.path_id,
            "child_id": child_id,
            "branch_state": branch_state,
            "total_paths": len(self.paths)
        })
        
        return child
    
    def advance_path(self, path_idx: int, new_state: Dict[str, Any]) -> bool:
        """Advance path to new state"""
        if path_idx >= len(self.paths):
            return False
        
        path = self.paths[path_idx]
        path.add_state(new_state)
        
        # Update coherence based on state transition
        coherence_change = self._calculate_coherence_change(
            path.states[-2] if len(path.states) > 1 else {},
            new_state
        )
        path.coherence *= coherence_change
        
        return True
    
    def _calculate_coherence_change(self, prev_state: Dict, new_state: Dict) -> float:
        """Calculate how coherent the state transition is"""
        # Simplified: check if new state builds on previous
        shared_keys = set(prev_state.keys()) & set(new_state.keys())
        coherence = len(shared_keys) / max(len(set(prev_state.keys()) | set(new_state.keys())), 1)
        return max(0.7, min(1.0, coherence + 0.3))
    
    def find_optimal_paths(self, top_n: int = 3) -> List[ExecutionPath]:
        """
        Find optimal paths based on multi-criteria scoring.
        "Optimal states of procession"
        """
        # Calculate scores for all paths
        for path in self.paths:
            path.calculate_score()
        
        # Sort by score
        sorted_paths = sorted(self.paths, key=lambda p: p.score, reverse=True)
        
        # Mark top N as optimal
        optimal = sorted_paths[:top_n]
        for path in optimal:
            path.is_optimal = True
        
        self.optimal_paths = optimal
        
        self._log_event("optimal_paths_selected", {
            "count": len(optimal),
            "scores": [p.score for p in optimal],
            "paths": [p.path_id for p in optimal]
        })
        
        return optimal
    
    def parallel_exploration(self, initial_state: Dict[str, Any], 
                           branches: int = 5, depth: int = 3) -> List[ExecutionPath]:
        """
        Perform parallel exploration from initial state.
        Creates multiple paths and advances them in parallel.
        """
        # Initialize root paths
        root_paths = []
        for i in range(branches):
            path = self.initialize_path(f"root-{i}", initial_state)
            root_paths.append(path)
        
        # Advance each path through decision tree
        for level in range(depth):
            for path_idx, path in enumerate(list(self.paths)):
                # Generate next state
                next_state = {
                    "level": level + 1,
                    "value": 0.5 + (path_idx * 0.1) - (level * 0.05),
                    "decision": f"choice_{path_idx}_{level}"
                }
                
                self.advance_path(path_idx, next_state)
                
                # Branch at some decision points
                if level < depth - 1 and path_idx % 2 == 0:
                    branch_state = {
                        "level": level + 1,
                        "value": next_state["value"] + 0.2,
                        "decision": f"branch_{path_idx}_{level}"
                    }
                    self.branch_path(path_idx, f"alt-{level}", branch_state)
        
        return root_paths
    
    def get_path_statistics(self) -> Dict[str, Any]:
        """Get statistics on path exploration"""
        if not self.paths:
            return {
                "total_paths": 0,
                "optimal_paths": 0,
                "average_score": 0.0,
                "average_coherence": 0.0
            }
        
        return {
            "total_paths": len(self.paths),
            "optimal_paths": len(self.optimal_paths),
            "average_score": sum(p.score for p in self.paths) / len(self.paths),
            "average_coherence": sum(p.coherence for p in self.paths) / len(self.paths),
            "max_score": max(p.score for p in self.paths),
            "total_states": sum(len(p.states) for p in self.paths)
        }
    
    def compare_paths(self, idx1: int, idx2: int) -> Dict[str, Any]:
        """Compare two paths for divergence analysis"""
        if idx1 >= len(self.paths) or idx2 >= len(self.paths):
            return {}
        
        path1 = self.paths[idx1]
        path2 = self.paths[idx2]
        
        return {
            "path1_id": path1.path_id,
            "path2_id": path2.path_id,
            "score_difference": abs(path1.score - path2.score),
            "coherence_difference": abs(path1.coherence - path2.coherence),
            "length_difference": abs(len(path1.states) - len(path2.states)),
            "both_optimal": path1.is_optimal and path2.is_optimal
        }
    
    def _log_event(self, event_type: str, data: Dict):
        """Log path exploration events"""
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


def optimize_procession_paths(initial_state: Dict[str, Any], 
                             branches: int = 5) -> Dict[str, Any]:
    """
    Main entry point: Explore and optimize multiple paths of procession
    """
    optimizer = MultiPathOptimizer()
    
    # Parallel exploration
    paths = optimizer.parallel_exploration(initial_state, branches=branches, depth=4)
    
    # Find optimal
    optimal = optimizer.find_optimal_paths(top_n=3)
    
    # Get statistics
    stats = optimizer.get_path_statistics()
    
    return {
        "initial_paths": len(paths),
        "total_paths_explored": stats["total_paths"],
        "optimal_paths": [p.to_dict() for p in optimal],
        "statistics": stats
    }


if __name__ == "__main__":
    # Test
    result = optimize_procession_paths(
        initial_state={"position": 0, "value": 0.5},
        branches=5
    )
    
    print("Multi-Path Optimization:")
    print(f"  Initial paths: {result['initial_paths']}")
    print(f"  Total explored: {result['total_paths_explored']}")
    print(f"  Optimal paths: {len(result['optimal_paths'])}")
    print(f"  Average score: {result['statistics']['average_score']:.3f}")
    print(f"\nTop optimal paths:")
    for i, path in enumerate(result['optimal_paths']):
        print(f"  {i+1}. {path['path_id']}: score={path['score']:.3f}, coherence={path['coherence']:.3f}")
