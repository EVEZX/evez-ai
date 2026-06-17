"""EVEZ Game Agent Infrastructure.

A comprehensive self-building game system implementing:
- Quantum-enhanced random number generation
- Threat detection (local and network)
- Pattern analysis and prediction
- Coherency synchronization and entanglement
- Wheel-rooted cognition (R1-R7 Piaget→Spiral Dynamics)
- Failure-Surface Cartography (FSC)
- Rollback shooter backend (60Hz/20Hz/250ms)
- Play Forever forensic episode engine
- Truth-sifting intent-asset bundler
- Self-building game mechanics
- Counter-intelligence psyops
- EVEZ666 voice clone

Usage:
    from evez_game import EVEZGame
    
    game = EVEZGame()
    game.start()
"""

__version__ = "1.0.0"
__author__ = "EVEZ666"

from .main import EVEZGame
from .quantum_rng import QuantumRNG, random_bytes, random_int, random_float
from .threat_engine import ThreatIntelligence, ThreatLevel, ThreatCategory
from .pattern_engine import PatternEngine, Pattern, Prediction
from .coherency_sync import CoherencySynchronizer, EntanglementManager
from .cognition_wheel import CognitiveWheel, CognitiveStage
from .fsc import FailureSurfaceCartographer, FailureDomain, FailureSeverity
from .rollback_engine import RollbackEngine, GameState, PlayerInput
from .play_forever import PlayForeverEngine, ForensicEpisode, LobbyType
from .truth_sifter import TruthSifter, Intent, Bundle, IntentType
from .self_building import SelfBuildingEngine, BuildTrigger, Lobby
from .psyops import PsyOpsController, Honeypot, DeceptionCampaign
from .evez_voice import EVEZVoice, VoiceMode
from .spine import append_event, read_events, lint
from .visualizer import visualize_spine

__all__ = [
    # Main
    "EVEZGame",
    
    # Core Systems
    "QuantumRNG",
    "random_bytes",
    "random_int", 
    "random_float",
    
    # Threat
    "ThreatIntelligence",
    "ThreatLevel",
    "ThreatCategory",
    
    # Pattern
    "PatternEngine",
    "Pattern",
    "Prediction",
    
    # Coherency
    "CoherencySynchronizer",
    "EntanglementManager",
    
    # Cognition
    "CognitiveWheel",
    "CognitiveStage",
    
    # FSC
    "FailureSurfaceCartographer",
    "FailureDomain",
    "FailureSeverity",
    
    # Rollback
    "RollbackEngine",
    "GameState",
    "PlayerInput",
    
    # Play Forever
    "PlayForeverEngine",
    "ForensicEpisode",
    "LobbyType",
    
    # Truth
    "TruthSifter",
    "Intent",
    "Bundle",
    "IntentType",
    
    # Self-Building
    "SelfBuildingEngine",
    "BuildTrigger",
    "Lobby",
    
    # PsyOps
    "PsyOpsController",
    "Honeypot",
    "DeceptionCampaign",
    
    # Voice
    "EVEZVoice",
    "VoiceMode",
    
    # Spine
    "append_event",
    "read_events",
    "lint",
    
    # Visualizer
    "visualize_spine",
]
