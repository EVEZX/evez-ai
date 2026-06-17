"""Rollback Shooter Backend - Deterministic Game State Management.

Implements:
- 60Hz tick rate for game logic
- 20Hz snapshot rate for state persistence
- 250ms rewind window for rollback
- Deterministic state serialization
- Hash-chained event log
"""

from __future__ import annotations

import hashlib
import json
import struct
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from .spine import append_event
from .quantum_rng import random_float


TICK_RATE = 60          # Hz - game logic update rate
SNAPSHOT_RATE = 20      # Hz - state persistence rate
REWIND_WINDOW_MS = 250  # ms - maximum rollback window


class InputType(Enum):
    """Types of player inputs."""
    MOVE = auto()
    AIM = auto()
    FIRE = auto()
    RELOAD = auto()
    USE = auto()
    JUMP = auto()
    CROUCH = auto()


@dataclass
class PlayerInput:
    """A single player input."""
    player_id: str
    input_type: InputType
    value: Any  # Vector2 for MOVE/AIM, bool for others
    timestamp: float
    sequence: int  # Input sequence number for ordering
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes for hashing."""
        data = {
            "player_id": self.player_id,
            "input_type": self.input_type.name,
            "value": str(self.value),
            "sequence": self.sequence
        }
        return json.dumps(data, sort_keys=True).encode()


@dataclass
class EntityState:
    """State of a game entity."""
    entity_id: str
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    health: float = 100.0
    is_alive: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_bytes(self) -> bytes:
        """Serialize to deterministic bytes."""
        data = struct.pack(
            "<9f?",
            *self.position,
            *self.velocity,
            *self.rotation,
            self.is_alive
        )
        data += struct.pack("<f", self.health)
        data += json.dumps(self.metadata, sort_keys=True).encode()
        return data


@dataclass
class GameState:
    """Complete game state at a point in time."""
    tick: int
    timestamp: float
    entities: Dict[str, EntityState] = field(default_factory=dict)
    inputs: List[PlayerInput] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    rng_seed: int = 0
    
    def hash(self) -> str:
        """Compute deterministic hash of state."""
        hasher = hashlib.sha256()
        hasher.update(struct.pack("<QI", int(self.timestamp * 1000), self.tick))
        
        for entity_id in sorted(self.entities.keys()):
            hasher.update(self.entities[entity_id].to_bytes())
        
        for inp in sorted(self.inputs, key=lambda i: i.sequence):
            hasher.update(inp.to_bytes())
        
        return hasher.hexdigest()[:32]
    
    def copy(self) -> "GameState":
        """Create deep copy of state."""
        return GameState(
            tick=self.tick,
            timestamp=self.timestamp,
            entities={eid: EntityState(**asdict(es)) for eid, es in self.entities.items()},
            inputs=list(self.inputs),
            events=list(self.events),
            rng_seed=self.rng_seed
        )


@dataclass
class Snapshot:
    """A persisted game state snapshot."""
    state: GameState
    hash: str = ""
    prev_hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self.state.hash()


class GameSimulation:
    """Deterministic game simulation."""
    
    def __init__(self):
        self.current_state = GameState(tick=0, timestamp=time.time())
        self.tick_duration = 1.0 / TICK_RATE
        self._entity_counter = 0
    
    def spawn_entity(self, position: Tuple[float, float, float] = None,
                     health: float = 100.0, **metadata) -> str:
        """Spawn a new entity."""
        self._entity_counter += 1
        entity_id = f"entity_{self._entity_counter}"
        
        self.current_state.entities[entity_id] = EntityState(
            entity_id=entity_id,
            position=position or (0.0, 0.0, 0.0),
            health=health,
            metadata=metadata
        )
        
        return entity_id
    
    def apply_input(self, inp: PlayerInput) -> None:
        """Apply a player input to the simulation."""
        entity = self.current_state.entities.get(inp.player_id)
        if not entity or not entity.is_alive:
            return
        
        if inp.input_type == InputType.MOVE:
            # value is (dx, dy) vector
            dx, dy = inp.value
            x, y, z = entity.position
            speed = 5.0 * self.tick_duration  # 5 units per second
            entity.position = (x + dx * speed, y + dy * speed, z)
        
        elif inp.input_type == InputType.AIM:
            # value is (pitch, yaw) angles
            pitch, yaw = inp.value
            entity.rotation = (pitch, yaw, 0.0)
        
        elif inp.input_type == InputType.FIRE:
            # Create projectile
            self._spawn_projectile(entity)
        
        elif inp.input_type == InputType.JUMP:
            vx, vy, vz = entity.velocity
            entity.velocity = (vx, vy, 10.0)  # Jump velocity
    
    def _spawn_projectile(self, source: EntityState) -> None:
        """Spawn a projectile from an entity."""
        proj_id = self.spawn_entity(
            position=source.position,
            health=1.0,
            projectile=True,
            owner=source.entity_id
        )
        
        # Set velocity based on aim direction
        pitch, yaw, _ = source.rotation
        speed = 50.0  # Projectile speed
        
        import math
        vx = speed * math.cos(pitch) * math.cos(yaw)
        vy = speed * math.cos(pitch) * math.sin(yaw)
        vz = speed * math.sin(pitch)
        
        self.current_state.entities[proj_id].velocity = (vx, vy, vz)
    
    def tick(self, inputs: List[PlayerInput] = None) -> GameState:
        """Advance simulation by one tick."""
        inputs = inputs or []
        
        # Sort inputs by sequence
        inputs.sort(key=lambda i: i.sequence)
        
        # Apply inputs
        for inp in inputs:
            self.apply_input(inp)
        
        # Update entities (physics)
        for entity in list(self.current_state.entities.values()):
            self._update_entity(entity)
        
        # Update tick counter
        self.current_state.tick += 1
        self.current_state.timestamp += self.tick_duration
        self.current_state.inputs = inputs
        
        return self.current_state.copy()
    
    def _update_entity(self, entity: EntityState) -> None:
        """Update entity physics."""
        if not entity.is_alive:
            return
        
        # Apply velocity
        x, y, z = entity.position
        vx, vy, vz = entity.velocity
        
        dt = self.tick_duration
        entity.position = (x + vx * dt, y + vy * dt, z + vz * dt)
        
        # Apply gravity
        if entity.metadata.get("projectile"):
            entity.velocity = (vx, vy, vz - 9.8 * dt)
        
        # Ground collision (simplified)
        if z < 0:
            entity.position = (x, y, 0)
            entity.velocity = (vx, vy, 0)
        
        # Check projectile collisions
        if entity.metadata.get("projectile"):
            self._check_projectile_collision(entity)
    
    def _check_projectile_collision(self, projectile: EntityState) -> None:
        """Check if projectile hits any entity."""
        for entity in self.current_state.entities.values():
            if entity.entity_id == projectile.entity_id:
                continue
            if entity.metadata.get("projectile"):
                continue
            if not entity.is_alive:
                continue
            
            # Simple distance check
            px, py, pz = projectile.position
            ex, ey, ez = entity.position
            
            dist = ((px-ex)**2 + (py-ey)**2 + (pz-ez)**2) ** 0.5
            
            if dist < 1.0:  # Hit radius
                # Apply damage
                entity.health -= 25.0
                if entity.health <= 0:
                    entity.is_alive = False
                
                # Destroy projectile
                projectile.is_alive = False
                
                # Log event
                self.current_state.events.append({
                    "type": "hit",
                    "projectile": projectile.entity_id,
                    "target": entity.entity_id,
                    "damage": 25.0,
                    "tick": self.current_state.tick
                })
                break


class RollbackBuffer:
    """Buffer for rollback-capable state storage."""
    
    def __init__(self, max_window_ms: int = REWIND_WINDOW_MS):
        self.max_window_ms = max_window_ms
        self.snapshots: List[Snapshot] = []
        self.input_history: Dict[int, List[PlayerInput]] = {}
        self._lock = threading.Lock()
    
    def push(self, state: GameState) -> Snapshot:
        """Push a new state snapshot."""
        snapshot = Snapshot(state=state)
        
        with self._lock:
            # Link to previous
            if self.snapshots:
                snapshot.prev_hash = self.snapshots[-1].hash
            
            self.snapshots.append(snapshot)
            
            # Store inputs
            self.input_history[state.tick] = list(state.inputs)
            
            # Prune old snapshots
            self._prune_old()
        
        return snapshot
    
    def _prune_old(self) -> None:
        """Remove snapshots outside rewind window."""
        if not self.snapshots:
            return
        
        current_time = self.snapshots[-1].state.timestamp
        cutoff_time = current_time - (self.max_window_ms / 1000.0)
        
        # Keep at least 10 snapshots
        while len(self.snapshots) > 10:
            if self.snapshots[0].state.timestamp < cutoff_time:
                old_tick = self.snapshots[0].state.tick
                self.snapshots.pop(0)
                if old_tick in self.input_history:
                    del self.input_history[old_tick]
            else:
                break
    
    def get_nearest_before(self, tick: int) -> Optional[Snapshot]:
        """Get nearest snapshot before or at given tick."""
        with self._lock:
            for snapshot in reversed(self.snapshots):
                if snapshot.state.tick <= tick:
                    return snapshot
        return None
    
    def get_inputs_since(self, tick: int) -> List[PlayerInput]:
        """Get all inputs since given tick."""
        with self._lock:
            inputs = []
            for t, inps in self.input_history.items():
                if t > tick:
                    inputs.extend(inps)
            return sorted(inputs, key=lambda i: i.sequence)


class RollbackEngine:
    """Main rollback engine managing game state and history."""
    
    def __init__(self, spine_path: Optional[Path] = None):
        self.simulation = GameSimulation()
        self.buffer = RollbackBuffer()
        self.spine_path = spine_path or Path("rollback_spine.jsonl")
        self.pending_inputs: List[PlayerInput] = []
        self._tick_thread: Optional[threading.Thread] = None
        self._stop_ticking = threading.Event()
        self._tick_callbacks: List[Callable[[GameState], None]] = []
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start the game tick loop."""
        self._stop_ticking.clear()
        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()
    
    def stop(self) -> None:
        """Stop the game tick loop."""
        self._stop_ticking.set()
        if self._tick_thread:
            self._tick_thread.join()
    
    def _tick_loop(self) -> None:
        """Main tick loop running at TICK_RATE."""
        next_tick = time.time()
        tick_duration = 1.0 / TICK_RATE
        
        while not self._stop_ticking.is_set():
            # Process pending inputs
            with self._lock:
                inputs = list(self.pending_inputs)
                self.pending_inputs = []
            
            # Tick simulation
            state = self.simulation.tick(inputs)
            
            # Snapshot at SNAPSHOT_RATE
            if state.tick % (TICK_RATE // SNAPSHOT_RATE) == 0:
                snapshot = self.buffer.push(state)
                self._log_snapshot(snapshot)
            
            # Notify callbacks
            for cb in self._tick_callbacks:
                try:
                    cb(state)
                except Exception:
                    pass
            
            # Wait for next tick
            next_tick += tick_duration
            sleep_time = next_tick - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _log_snapshot(self, snapshot: Snapshot) -> None:
        """Log snapshot to spine."""
        event = {
            "type": "snapshot",
            "tick": snapshot.state.tick,
            "hash": snapshot.hash,
            "prev_hash": snapshot.prev_hash,
            "entity_count": len(snapshot.state.entities),
            "event_count": len(snapshot.state.events)
        }
        append_event(self.spine_path, event)
    
    def submit_input(self, inp: PlayerInput) -> None:
        """Submit a player input."""
        with self._lock:
            self.pending_inputs.append(inp)
    
    def rollback(self, to_tick: int, corrected_inputs: List[PlayerInput]) -> GameState:
        """Rollback to given tick and replay with corrected inputs."""
        # Find nearest snapshot
        snapshot = self.buffer.get_nearest_before(to_tick)
        
        if not snapshot:
            raise ValueError(f"No snapshot available for tick {to_tick}")
        
        # Restore state
        self.simulation.current_state = snapshot.state.copy()
        
        # Get inputs since snapshot
        inputs_since = self.buffer.get_inputs_since(snapshot.state.tick)
        
        # Merge corrected inputs
        all_inputs = inputs_since + corrected_inputs
        
        # Sort by sequence
        all_inputs.sort(key=lambda i: i.sequence)
        
        # Replay ticks
        current_tick = snapshot.state.tick
        while current_tick < self.simulation.current_state.tick:
            tick_inputs = [i for i in all_inputs if i.sequence == current_tick]
            self.simulation.tick(tick_inputs)
            current_tick += 1
        
        return self.simulation.current_state
    
    def on_tick(self, callback: Callable[[GameState], None]) -> None:
        """Register tick callback."""
        self._tick_callbacks.append(callback)
    
    def get_current_state(self) -> GameState:
        """Get current game state."""
        return self.simulation.current_state.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "tick_rate": TICK_RATE,
            "snapshot_rate": SNAPSHOT_RATE,
            "rewind_window_ms": REWIND_WINDOW_MS,
            "current_tick": self.simulation.current_state.tick,
            "entity_count": len(self.simulation.current_state.entities),
            "buffered_snapshots": len(self.buffer.snapshots),
            "buffered_inputs": len(self.buffer.input_history)
        }


# Convenience functions
_engine: Optional[RollbackEngine] = None


def initialize(spine_path: Optional[Path] = None) -> RollbackEngine:
    """Initialize global rollback engine."""
    global _engine
    _engine = RollbackEngine(spine_path)
    return _engine


def get_engine() -> RollbackEngine:
    """Get global rollback engine."""
    if _engine is None:
        return initialize()
    return _engine
