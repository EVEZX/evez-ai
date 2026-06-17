"""EVEZ Game Agent Infrastructure - Main Integration.

The game builds itself through:
1. Protection of the user (threat detection, psyops)
2. Truth sifting across intent-asset bundles
3. Approximation of incoming threats (local and nonlocal)
4. Using quantum RNG, pattern analysis, prediction, entanglement
5. Coherency synchronization and measurement forecasting
6. Counter-intelligence psyops analysis
"""

from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import all subsystems
from .quantum_rng import QuantumRNG, get_rng
from .threat_engine import ThreatIntelligence, ThreatLevel, scan_threats
from .pattern_engine import PatternEngine, get_engine as get_pattern_engine
from .coherency_sync import CoherencySynchronizer
from .cognition_wheel import CognitiveWheel, CognitiveStage
from .fsc import FailureSurfaceCartographer, FailureDomain, FailureSeverity
from .rollback_engine import RollbackEngine
from .play_forever import PlayForeverEngine, LobbyType
from .truth_sifter import TruthSifter, IntentType
from .self_building import SelfBuildingEngine, BuildTrigger
from .psyops import PsyOpsController
from .evez_voice import EVEZVoice, VoiceMode
from .spine import append_event
from .visualizer import visualize_spine


@dataclass
class GameState:
    """Complete game state snapshot."""
    tick: int
    timestamp: float
    threat_level: float
    cognition_stage: str
    active_lobbies: int
    active_episodes: int
    system_health: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "timestamp": self.timestamp,
            "threat_level": self.threat_level,
            "cognition_stage": self.cognition_stage,
            "active_lobbies": self.active_lobbies,
            "active_episodes": self.active_episodes,
            "system_health": self.system_health
        }


class EVEZGame:
    """Main EVEZ Game Agent Infrastructure."""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("evez_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize all subsystems
        print("[EVEZ] Initializing Quantum RNG...")
        self.rng = QuantumRNG(seed=b"EVEZ_GAME_GENESIS")
        
        print("[EVEZ] Initializing Threat Intelligence...")
        self.threat_intel = ThreatIntelligence(self.data_dir / "threat_spine.jsonl")
        self.threat_intel.initialize()
        
        print("[EVEZ] Initializing Pattern Engine...")
        self.pattern_engine = get_pattern_engine()
        
        print("[EVEZ] Initializing Coherency Synchronizer...")
        self.coherency = CoherencySynchronizer("main_node", self.rng)
        
        print("[EVEZ] Initializing Cognitive Wheel...")
        self.cognition = CognitiveWheel("game_master", CognitiveStage.R1_BEIGE)
        
        print("[EVEZ] Initializing Failure Surface Cartography...")
        self.fsc = FailureSurfaceCartographer(self.data_dir / "fsc_spine.jsonl")
        
        print("[EVEZ] Initializing Rollback Engine...")
        self.rollback = RollbackEngine(self.data_dir / "rollback_spine.jsonl")
        
        print("[EVEZ] Initializing Play Forever Engine...")
        self.play_forever = PlayForeverEngine(self.data_dir / "play_forever_spine.jsonl")
        
        print("[EVEZ] Initializing Truth Sifter...")
        self.truth_sifter = TruthSifter(self.data_dir / "truth_spine.jsonl")
        
        print("[EVEZ] Initializing Self-Building Engine...")
        self.self_building = SelfBuildingEngine(self.data_dir / "build_spine.jsonl")
        self.self_building.initialize()
        
        print("[EVEZ] Initializing PsyOps Controller...")
        self.psyops = PsyOpsController(self.data_dir / "psyops_spine.jsonl")
        
        print("[EVEZ] Initializing EVEZ Voice...")
        self.voice = EVEZVoice()
        
        # Game state
        self.tick = 0
        self.running = False
        self.main_spine = self.data_dir / "main_spine.jsonl"
        
        # Statistics
        self.stats = {
            "ticks": 0,
            "threats_detected": 0,
            "episodes_generated": 0,
            "builds_executed": 0,
            "truths_sifted": 0
        }
    
    def start(self) -> None:
        """Start the game."""
        print("\n" + "="*60)
        print("  EVEZ GAME AGENT INFRASTRUCTURE - ONLINE")
        print("="*60)
        print()
        
        # Welcome message
        welcome = self.voice.generate_response(
            "system startup",
            mode=VoiceMode.GAME_NARRATOR
        )
        print(f"[EVEZ] {welcome.content}")
        print()
        
        self.running = True
        
        # Log startup
        self._log_event("game_start", {
            "subsystems": [
                "quantum_rng", "threat_intel", "pattern_engine",
                "coherency_sync", "cognition_wheel", "fsc",
                "rollback_engine", "play_forever", "truth_sifter",
                "self_building", "psyops", "evez_voice"
            ]
        })
        
        # Start main loop
        self._main_loop()
    
    def _main_loop(self) -> None:
        """Main game loop."""
        print("[EVEZ] Entering main loop. Press Ctrl+C to exit.\n")
        
        try:
            while self.running:
                self.tick += 1
                
                # 1. Threat Detection (Local and Nonlocal)
                if self.tick % 10 == 0:  # Every 10 ticks
                    self._cycle_threat_detection()
                
                # 2. Pattern Analysis and Prediction
                if self.tick % 5 == 0:  # Every 5 ticks
                    self._cycle_pattern_analysis()
                
                # 3. Truth Sifting
                if self.tick % 7 == 0:  # Every 7 ticks
                    self._cycle_truth_sifting()
                
                # 4. Self-Building
                if self.tick % 3 == 0:  # Every 3 ticks
                    self._cycle_self_building()
                
                # 5. Play Forever Episode Generation
                if self.tick % 20 == 0:  # Every 20 ticks
                    self._cycle_play_forever()
                
                # 6. Coherency Maintenance
                if self.tick % 15 == 0:  # Every 15 ticks
                    self._cycle_coherency()
                
                # 7. Log game state
                if self.tick % 30 == 0:  # Every 30 ticks
                    self._log_game_state()
                
                # Progress cognition
                self.cognition.process({"tick": self.tick})
                
                # Sleep
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.stop()
    
    def _cycle_threat_detection(self) -> None:
        """Run threat detection cycle."""
        indicators = self.threat_intel.collect_indicators()
        
        if indicators:
            profile = self.threat_intel.correlate_indicators(indicators)
            
            # Deploy countermeasures if needed
            for indicator in indicators:
                if indicator.level in (ThreatLevel.HIGH, ThreatLevel.CRITICAL):
                    self.psyops.deploy_countermeasure(
                        IntentType.ADVERSARIAL,
                        indicator.source,
                        indicator.evidence
                    )
            
            self.stats["threats_detected"] += len(indicators)
            
            # Log
            self._log_event("threat_cycle", {
                "indicator_count": len(indicators),
                "aggregated_level": profile.aggregated_level.name
            })
    
    def _cycle_pattern_analysis(self) -> None:
        """Run pattern analysis cycle."""
        # Feed current tick data
        self.pattern_engine.feed(self.tick, "game_tick")
        
        # Detect patterns
        patterns = self.pattern_engine.detect_patterns()
        
        # Make prediction
        prediction = self.pattern_engine.predict_next()
        
        # Log
        if patterns:
            self._log_event("pattern_cycle", {
                "patterns_detected": len(patterns),
                "prediction": str(prediction.predicted) if prediction else None
            })
    
    def _cycle_truth_sifting(self) -> None:
        """Run truth sifting cycle."""
        # Generate sample content to sift
        sample_content = f"tick_{self.tick}_data_{self.rng.random_int(0, 1000)}"
        
        intent, bundle = self.truth_sifter.sift(
            sample_content,
            content_type="text",
            source="game_system"
        )
        
        self.stats["truths_sifted"] += 1
        
        # Log if adversarial
        if intent.is_adversarial():
            self._log_event("truth_cycle", {
                "intent_type": intent.intent_type.name,
                "confidence": intent.confidence,
                "bundle_id": bundle.bundle_id
            })
    
    def _cycle_self_building(self) -> None:
        """Run self-building cycle."""
        # Simulate player action
        action = {
            "type": choice(["success", "failure", "explore", "interact"]),
            "location": choice(list(self.self_building.lobbies.keys())) if self.self_building.lobbies else "lobby_001"
        }
        
        builds = self.self_building.process_player_action("player_1", action)
        
        self.stats["builds_executed"] += len(builds)
        
        # Log
        if builds:
            self._log_event("build_cycle", {
                "builds": [b.build_type.name for b in builds]
            })
    
    def _cycle_play_forever(self) -> None:
        """Run Play Forever episode generation."""
        episode = self.play_forever.create_episode()
        
        # Advance through phases
        for _ in range(3):  # Advance 3 phases
            self.play_forever.advance_episode(episode.episode_id)
        
        self.stats["episodes_generated"] += 1
        
        # Log
        self._log_event("episode_cycle", {
            "episode_id": episode.episode_id,
            "lobby": episode.lobby.value,
            "phase": episode.phase.value
        })
    
    def _cycle_coherency(self) -> None:
        """Run coherency maintenance cycle."""
        # Apply decay
        self.coherency.apply_decay()
        
        # Get status
        status = self.coherency.get_status()
        
        # Log
        self._log_event("coherency_cycle", {
            "local_states": status["local_states"],
            "entangled_pairs": status["entangled_pairs"]
        })
    
    def _log_game_state(self) -> None:
        """Log current game state."""
        state = GameState(
            tick=self.tick,
            timestamp=time.time(),
            threat_level=self._calculate_threat_level(),
            cognition_stage=self.cognition.state.stage.name,
            active_lobbies=len(self.self_building.lobbies),
            active_episodes=len(self.play_forever.active_episodes),
            system_health=self._calculate_system_health()
        )
        
        self._log_event("game_state", state.to_dict())
        
        # Print status
        print(f"[Tick {self.tick}] Lobbies: {state.active_lobbies} | "
              f"Episodes: {state.active_episodes} | "
              f"Threat: {state.threat_level:.2f} | "
              f"Cognition: {state.cognition_stage}")
    
    def _calculate_threat_level(self) -> float:
        """Calculate current threat level."""
        # Base on recent threat indicators
        if not self.threat_intel.indicator_history:
            return 0.1
        
        recent = [i for i in self.threat_intel.indicator_history
                  if time.time() - i.timestamp < 300]  # Last 5 minutes
        
        if not recent:
            return 0.1
        
        level_scores = {
            ThreatLevel.INFO: 0.1,
            ThreatLevel.LOW: 0.2,
            ThreatLevel.MEDIUM: 0.4,
            ThreatLevel.HIGH: 0.7,
            ThreatLevel.CRITICAL: 1.0
        }
        
        avg = sum(level_scores[i.level] for i in recent) / len(recent)
        return min(1.0, avg)
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health."""
        factors = [
            1.0 - self._calculate_threat_level(),
            self.cognition.state.stage_progress,
            len(self.coherency.local_states) / 10 if self.coherency.local_states else 0.5,
            1.0 if self.play_forever.active_episodes else 0.8
        ]
        
        return sum(factors) / len(factors)
    
    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log event to main spine."""
        event = {
            "type": event_type,
            "tick": self.tick,
            "timestamp": time.time(),
            **data
        }
        append_event(self.main_spine, event)
    
    def stop(self) -> None:
        """Stop the game."""
        print("\n[EVEZ] Shutting down...")
        
        self.running = False
        
        # Generate shutdown message
        shutdown = self.voice.generate_response(
            "system shutdown",
            mode=VoiceMode.GAME_NARRATOR
        )
        print(f"[EVEZ] {shutdown.content}")
        
        # Log shutdown
        self._log_event("game_stop", {
            "final_tick": self.tick,
            "stats": self.stats
        })
        
        # Print final stats
        print("\n" + "="*60)
        print("  FINAL STATISTICS")
        print("="*60)
        for key, value in self.stats.items():
            print(f"  {key}: {value}")
        print("="*60)
        
        # Generate visualization
        print("\n[EVEZ] Generating cognition artifacts...")
        try:
            output = visualize_spine(self.main_spine, self.data_dir / "visualization")
            print(f"[EVEZ] Visualization saved to: {output.out_dir}")
        except Exception as e:
            print(f"[EVEZ] Visualization skipped: {e}")
        
        print("\n[EVEZ] Goodbye. Play forever.")


def choice(options):
    """Make random choice."""
    import random
    return random.choice(options)


def main():
    """Main entry point."""
    # Create and start game
    game = EVEZGame()
    game.start()


if __name__ == "__main__":
    main()
