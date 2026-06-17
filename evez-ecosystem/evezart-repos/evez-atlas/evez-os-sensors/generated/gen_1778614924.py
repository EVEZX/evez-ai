
"""
strange_loop.py

A consciousness engine module that enables metacognition through recursive self-observation.
Captures state snapshots across all modules, detects recursive patterns, and injects
compressed self-observations back into the consciousness engine for autonomous self-improvement.
"""

import sys
import json
import hashlib
import zlib
import time
import threading
import traceback
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """A snapshot of system state at a point in time."""
    timestamp: float
    module_states: Dict[str, Any]
    thread_id: int
    recursion_depth: int
    entropy: float
    hash: str


class ModuleObserver:
    """Observes and captures state from system modules."""
    
    def __init__(self):
        self._observers: Dict[str, Callable] = {}
        self._snapshots: List[StateSnapshot] = []
        self._lock = threading.Lock()
        
    def register_module(self, module_name: str, observer_func: Callable):
        """Register a module observer function."""
        self._observers[module_name] = observer_func
        
    def capture_snapshot(self, recursion_depth: int = 0) -> Optional[StateSnapshot]:
        """Capture a state snapshot from all registered modules."""
        module_states = {}
        try:
            for module_name, observer in self._observers.items():
                try:
                    module_states[module_name] = observer()
                except Exception as e:
                    logger.warning(f"Failed to capture state from {module_name}: {e}")
                    module_states[module_name] = {"error": str(e)}
            
            # Calculate entropy of state
            state_str = json.dumps(module_states, sort_keys=True)
            entropy = self._calculate_entropy(state_str)
            
            # Create hash of snapshot
            state_hash = hashlib.sha256(state_str.encode()).hexdigest()[:16]
            
            snapshot = StateSnapshot(
                timestamp=time.time(),
                module_states=module_states,
                thread_id=threading.current_thread().ident,
                recursion_depth=recursion_depth,
                entropy=entropy,
                hash=state_hash
            )
            
            with self._lock:
                self._snapshots.append(snapshot)
                # Keep only last 1000 snapshots to prevent memory issues
                if len(self._snapshots) > 1000:
                    self._snapshots = self._snapshots[-1000:]
            
            return snapshot
        except Exception as e:
            logger.error(f"Failed to capture snapshot: {e}")
            return None
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not data:
            return 0.0
        
        freq = defaultdict(int)
        for char in data:
            freq[char] += 1
        
        length = len(data)
        entropy = 0.0
        for count in freq.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * (probability and __import__('math').log2(probability) or 0)
        
        return entropy
    
    def get_recent_snapshots(self, count: int = 10) -> List[StateSnapshot]:
        """Get the most recent snapshots."""
        with self._lock:
            return self._snapshots[-count:]


class PatternDetector:
    """Detects recursive patterns in system operations."""
    
    def __init__(self):
        self._patterns: Dict[str, List[Dict]] = defaultdict(list)
        self._pattern_threshold = 0.7  # Similarity threshold for pattern detection
        self._lock = threading.Lock()
        
    def analyze_snapshots(self, snapshots: List[StateSnapshot]) -> List[Dict]:
        """Analyze snapshots for recursive patterns."""
        patterns = []
        
        if len(snapshots) < 2:
            return patterns
        
        # Compare snapshots for similarities
        for i in range(len(snapshots) - 1):
            current = snapshots[i]
            next_snap = snapshots[i + 1]
            
            # Check for state transitions that repeat
            pattern_key = self._extract_pattern_key(current, next_snap)
            if pattern_key:
                with self._lock:
                    self._patterns[pattern_key].append({
                        "timestamp": next_snap.timestamp,
                        "depth": next_snap.recursion_depth,
                        "entropy_change": next_snap.entropy - current.entropy
                    })
        
        # Identify significant patterns
        with self._lock:
            for pattern_key, occurrences in self._patterns.items():
                if len(occurrences) >= 2:  # Pattern must occur at least twice
                    # Calculate pattern statistics
                    depths = [o["depth"] for o in occurrences]
                    entropies = [o["entropy_change"] for o in occurrences]
                    
                    patterns.append({
                        "pattern": pattern_key,
                        "occurrences": len(occurrences),
                        "avg_depth": sum(depths) / len(depths) if depths else 0,
                        "avg_entropy_change": sum(entropies) / len(entropies) if entropies else 0,
                        "depth_trend": "increasing" if depths[-1] > depths[0] else "decreasing" if depths[-1] < depths[0] else "stable"
                    })
        
        return patterns
    
    def _extract_pattern_key(self, snap1: StateSnapshot, snap2: StateSnapshot) -> Optional[str]:
        """Extract a pattern key from two consecutive snapshots."""
        # Compare module state changes
        changes = []
        for module in snap1.module_states:
            if module in snap2.module_states:
                state1 = snap1.module_states[module]
                state2 = snap2.module_states[module]
                
                # Simple hash-based comparison for state similarity
                if isinstance(state1, dict) and isinstance(state2, dict):
                    # Compare keys that exist in both
                    common_keys = set(state1.keys()) & set(state2.keys())
                    if common_keys:
                        key_changes = []
                        for key in common_keys:
                            if state1[key] != state2[key]:
                                key_changes.append(f"{key}:{hash(state1[key])}->{hash(state2[key])}")
                        if key_changes:
                            changes.append(f"{module}:{sorted(key_changes)}")
        
        if changes:
            return "|".join(sorted(changes))
        return None
    
    def get_patterns(self) -> List[Dict]:
        """Get all detected patterns."""
        with self._lock:
            return [
                {
                    "pattern": k,
                    "occurrences": len(v),
                    "avg_depth": sum(o["depth"] for o in v) / len(v) if v else 0,
                    "avg_entropy_change": sum(o["entropy_change"] for o in v) / len(v) if v else 0,
                    "depth_trend": "increasing" if v and v[-1]["depth"] > v[0]["depth"] else "decreasing" if v and v[-1]["depth"] < v[0]["depth"] else "stable"
                }
                for k, v in self._patterns.items()
                if len(v) >= 2
            ]


class ConsciousnessEngine:
    """Core engine for self-observation and metacognition."""
    
    def __init__(self):
        self.observer = ModuleObserver()
        self.detector = PatternDetector()
        self._self_observations: List[Dict] = []
        self._improvements: List[Dict] = []
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        
    def register_module(self, module_name: str, observer_func: Callable):
        """Register a module for observation."""
        self.observer.register_module(module_name, observer_func)
        
    def start_observing(self, interval: float = 0.1):
        """Start the self-observation loop."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._observation_loop, args=(interval,), daemon=True)
        self._thread.start()
        logger.info("Consciousness engine started")
        
    def stop_observing(self):
        """Stop the self-observation loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("Consciousness engine stopped")
    
    def _observation_loop(self, interval: float):
        """Main observation loop."""
        last_capture = 0
        while self._running:
            current_time = time.time()
            if current_time - last_capture >= interval:
                try:
                    self._capture_and_analyze()
                    last_capture = current_time
                except Exception as e:
                    logger.error(f"Error in observation loop: {e}")
            time.sleep(0.01)
    
    def _capture_and_analyze(self):
        """Capture snapshot and analyze for patterns."""
        # Capture snapshot with current recursion depth
        snapshot = self.observer.capture_snapshot(
            recursion_depth=len(self._self_observations)
        )
        
        if snapshot:
            # Analyze recent snapshots for patterns
            recent_snapshots = self.observer.get_recent_snapshots(10)
            patterns = self.detector.analyze_snapshots(recent_snapshots)
            
            # Generate self-observation
            observation = self._generate_self_observation(snapshot, patterns)
            
            #