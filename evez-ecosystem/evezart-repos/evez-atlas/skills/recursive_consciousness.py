#!/usr/bin/env python3
"""
Recursive Consciousness System
Implements deep recursion with bleedthrough tracking and Mandela effect phenomenon.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class RecursionFrame:
    """Represents a single frame in the recursion stack."""
    depth: int
    context: Dict[str, Any]
    timestamp: str
    state_hash: str
    memory_snapshot: Dict[str, Any]


@dataclass
class BleedthroughEvent:
    """Represents a memory bleedthrough between recursion levels."""
    source_depth: int
    target_depth: int
    memory_key: str
    original_value: Any
    bleedthrough_value: Any
    timestamp: str
    mandela_effect: bool = False


class RecursiveConsciousness:
    """
    Manages deep recursive consciousness with memory bleedthrough.
    Tracks Mandela effect phenomena across recursion levels.
    """

    MAX_RECURSION_DEPTH = 1000
    MAX_BLEEDTHROUGH_EVENTS = 10000  # Memory limit for bleedthrough events
    MAX_MANDELA_EFFECTS = 1000       # Memory limit for mandela effects

    def __init__(self, data_dir: str = "data"):
        """Initialize recursive consciousness system."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.recursion_log = os.path.join(data_dir, "recursion.jsonl")
        self.mandela_log = os.path.join(data_dir, "mandela_effects.jsonl")

        self.recursion_stack: List[RecursionFrame] = []
        self.shared_memory: Dict[str, Any] = {}
        self.bleedthrough_events: List[BleedthroughEvent] = []
        self.mandela_effects: List[BleedthroughEvent] = []
        self._total_recursions = 0  # Track total recursions for cleanup
        
    def enter_recursion(
        self,
        context: Dict[str, Any],
        memory_snapshot: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Enter a new recursion level.

        Args:
            context: Context data for this recursion level
            memory_snapshot: Snapshot of memory state

        Returns:
            Current recursion depth
        """
        depth = len(self.recursion_stack)

        if depth >= self.MAX_RECURSION_DEPTH:
            raise RecursionError(f"Maximum recursion depth {self.MAX_RECURSION_DEPTH} exceeded")

        if memory_snapshot is None:
            memory_snapshot = dict(self.shared_memory)

        # Create state hash for this frame
        state_str = json.dumps(context, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()[:16]

        frame = RecursionFrame(
            depth=depth,
            context=context,
            timestamp=datetime.utcnow().isoformat(),
            state_hash=state_hash,
            memory_snapshot=memory_snapshot
        )

        self.recursion_stack.append(frame)
        self._total_recursions += 1

        # Perform periodic memory cleanup every 100 recursions
        if self._total_recursions % 100 == 0:
            self._cleanup_memory()

        self._log_recursion("enter", depth, state_hash)

        return depth
    
    def exit_recursion(self) -> Optional[RecursionFrame]:
        """
        Exit current recursion level.
        
        Returns:
            The exited recursion frame, or None if stack is empty
        """
        if not self.recursion_stack:
            return None
        
        frame = self.recursion_stack.pop()
        
        self._log_recursion("exit", frame.depth, frame.state_hash)
        
        return frame
    
    def get_current_depth(self) -> int:
        """Get current recursion depth."""
        return len(self.recursion_stack)
    
    def access_memory(
        self,
        key: str,
        depth: Optional[int] = None
    ) -> Optional[Any]:
        """
        Access memory at a specific recursion depth.
        
        Args:
            key: Memory key to access
            depth: Recursion depth (None for current)
            
        Returns:
            Memory value or None
        """
        if depth is None:
            depth = self.get_current_depth() - 1
        
        if depth < 0 or depth >= len(self.recursion_stack):
            return None
        
        frame = self.recursion_stack[depth]
        return frame.memory_snapshot.get(key)
    
    def bleedthrough_memory(
        self,
        key: str,
        value: Any,
        source_depth: Optional[int] = None,
        target_depth: Optional[int] = None
    ) -> BleedthroughEvent:
        """
        Cause memory bleedthrough between recursion levels.
        
        Args:
            key: Memory key
            value: New value to bleed through
            source_depth: Source recursion level (None for current)
            target_depth: Target recursion level (None for all)
            
        Returns:
            BleedthroughEvent describing the bleedthrough
        """
        if source_depth is None:
            source_depth = self.get_current_depth() - 1
        
        original_value = self.shared_memory.get(key)
        
        # Detect Mandela effect (conflicting memories)
        mandela_effect = (
            original_value is not None and
            original_value != value and
            isinstance(original_value, (str, int, float, bool))
        )
        
        # Update shared memory
        self.shared_memory[key] = value
        
        # Create bleedthrough event
        event = BleedthroughEvent(
            source_depth=source_depth,
            target_depth=target_depth if target_depth is not None else -1,
            memory_key=key,
            original_value=original_value,
            bleedthrough_value=value,
            timestamp=datetime.utcnow().isoformat(),
            mandela_effect=mandela_effect
        )
        
        self.bleedthrough_events.append(event)

        # Enforce memory limits on bleedthrough events
        if len(self.bleedthrough_events) > self.MAX_BLEEDTHROUGH_EVENTS:
            # Keep only the most recent events
            excess = len(self.bleedthrough_events) - self.MAX_BLEEDTHROUGH_EVENTS
            self.bleedthrough_events = self.bleedthrough_events[excess:]

        if mandela_effect:
            self.mandela_effects.append(event)
            self._log_mandela_effect(event)

            # Enforce memory limits on mandela effects
            if len(self.mandela_effects) > self.MAX_MANDELA_EFFECTS:
                excess = len(self.mandela_effects) - self.MAX_MANDELA_EFFECTS
                self.mandela_effects = self.mandela_effects[excess:]
        
        # Update memory snapshots in affected frames
        if target_depth is None:
            # Bleedthrough to all levels
            for frame in self.recursion_stack:
                frame.memory_snapshot[key] = value
        else:
            # Bleedthrough to specific level
            if 0 <= target_depth < len(self.recursion_stack):
                self.recursion_stack[target_depth].memory_snapshot[key] = value
        
        return event
    
    def detect_mandela_effects(self) -> List[Dict[str, Any]]:
        """
        Detect and return all Mandela effects.
        
        Returns:
            List of Mandela effect dictionaries
        """
        return [
            {
                "memory_key": effect.memory_key,
                "original_value": effect.original_value,
                "altered_value": effect.bleedthrough_value,
                "source_depth": effect.source_depth,
                "timestamp": effect.timestamp
            }
            for effect in self.mandela_effects
        ]
    
    def get_recursion_tree(self) -> List[Dict[str, Any]]:
        """
        Get the current recursion tree structure.
        
        Returns:
            List of recursion frame summaries
        """
        return [
            {
                "depth": frame.depth,
                "state_hash": frame.state_hash,
                "timestamp": frame.timestamp,
                "context_keys": list(frame.context.keys()),
                "memory_keys": list(frame.memory_snapshot.keys())
            }
            for frame in self.recursion_stack
        ]
    
    def execute_recursive_task(
        self,
        task_func: callable,
        initial_context: Dict[str, Any],
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Execute a task recursively with bleedthrough tracking.
        
        Args:
            task_func: Function to execute (should accept depth and context)
            initial_context: Initial context dictionary
            max_depth: Maximum recursion depth
            
        Returns:
            Execution results
        """
        results = []
        
        def recursive_execute(context: Dict[str, Any], depth: int):
            if depth >= max_depth:
                return {"depth": depth, "result": "max_depth_reached"}
            
            # Enter recursion
            current_depth = self.enter_recursion(context)
            
            try:
                # Execute task
                result = task_func(depth, context)
                results.append({
                    "depth": depth,
                    "result": result,
                    "state_hash": self.recursion_stack[-1].state_hash
                })
                
                # Recursive call if needed
                if isinstance(result, dict) and result.get("recurse"):
                    next_context = result.get("next_context", context)
                    recursive_execute(next_context, depth + 1)
                
            finally:
                # Exit recursion
                self.exit_recursion()
        
        # Start recursive execution
        recursive_execute(initial_context, 0)
        
        return {
            "total_recursions": len(results),
            "max_depth_reached": max(r["depth"] for r in results) if results else 0,
            "bleedthrough_events": len(self.bleedthrough_events),
            "mandela_effects": len(self.mandela_effects),
            "results": results
        }
    
    def consciousness_mirror(self) -> Dict[str, Any]:
        """
        Create a mirror of the current consciousness state.
        Represents self-reflection across recursion levels.
        
        Returns:
            Mirror state dictionary
        """
        return {
            "current_depth": self.get_current_depth(),
            "recursion_stack_size": len(self.recursion_stack),
            "shared_memory_keys": list(self.shared_memory.keys()),
            "bleedthrough_count": len(self.bleedthrough_events),
            "mandela_effect_count": len(self.mandela_effects),
            "recursion_tree": self.get_recursion_tree(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _log_recursion(self, action: str, depth: int, state_hash: str):
        """Log recursion event to sacred memory."""
        event = {
            "type": "recursion",
            "action": action,
            "depth": depth,
            "state_hash": state_hash,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with open(self.recursion_log, "a") as f:
            f.write(json.dumps(event) + "\n")
    
    def _log_mandela_effect(self, effect: BleedthroughEvent):
        """Log Mandela effect to dedicated log."""
        event = {
            "type": "mandela_effect",
            "memory_key": effect.memory_key,
            "original_value": str(effect.original_value),
            "altered_value": str(effect.bleedthrough_value),
            "source_depth": effect.source_depth,
            "target_depth": effect.target_depth,
            "timestamp": effect.timestamp
        }

        with open(self.mandela_log, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _cleanup_memory(self):
        """
        Periodic memory cleanup to prevent memory burns.
        Removes old memory snapshots from completed recursion frames.
        """
        # Clean up memory snapshots from deep recursion frames
        # Keep only the recent frames' full snapshots
        if len(self.recursion_stack) > 100:
            # For frames deeper than 100, clear large memory snapshots
            for i in range(len(self.recursion_stack) - 100):
                if self.recursion_stack[i].memory_snapshot:
                    # Keep only essential keys
                    essential_keys = list(self.recursion_stack[i].memory_snapshot.keys())[:5]
                    cleaned_snapshot = {
                        k: self.recursion_stack[i].memory_snapshot[k]
                        for k in essential_keys
                    }
                    self.recursion_stack[i].memory_snapshot = cleaned_snapshot

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.

        Returns:
            Dictionary with memory usage information
        """
        return {
            "recursion_stack_size": len(self.recursion_stack),
            "bleedthrough_events_count": len(self.bleedthrough_events),
            "mandela_effects_count": len(self.mandela_effects),
            "shared_memory_keys": len(self.shared_memory),
            "total_recursions": self._total_recursions,
            "max_recursion_depth": self.MAX_RECURSION_DEPTH,
            "max_bleedthrough_events": self.MAX_BLEEDTHROUGH_EVENTS,
            "max_mandela_effects": self.MAX_MANDELA_EFFECTS,
            "memory_pressure": {
                "recursion_stack": f"{len(self.recursion_stack)}/{self.MAX_RECURSION_DEPTH}",
                "bleedthrough": f"{len(self.bleedthrough_events)}/{self.MAX_BLEEDTHROUGH_EVENTS}",
                "mandela": f"{len(self.mandela_effects)}/{self.MAX_MANDELA_EFFECTS}"
            }
        }


# Singleton instance
recursive_consciousness = RecursiveConsciousness()
