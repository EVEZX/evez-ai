#!/usr/bin/env python3
"""Launcher script for EVEZ Game Agent Infrastructure.

This script properly sets up the package context and runs the game.
"""

import sys
import os
from pathlib import Path

# Add the output directory to path
output_dir = Path(__file__).parent
sys.path.insert(0, str(output_dir))

# Create the evez_game package namespace
import types
evez_game = types.ModuleType('evez_game')
evez_game.__path__ = [str(output_dir / 'evez_game')]
sys.modules['evez_game'] = evez_game

# Load all modules
import importlib.util

def load_module(module_name, file_path):
    """Load a module and add it to evez_game package."""
    spec = importlib.util.spec_from_file_location(
        f'evez_game.{module_name}', 
        file_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[f'evez_game.{module_name}'] = module
    spec.loader.exec_module(module)
    setattr(evez_game, module_name, module)
    return module

# Load modules in dependency order
evez_dir = output_dir / 'evez_game'

print("[Launcher] Loading EVEZ Game modules...")

# Core (no dependencies)
load_module('canonical', evez_dir / 'canonical.py')
load_module('quantum_rng', evez_dir / 'quantum_rng.py')

# Spine (depends on canonical)
load_module('spine', evez_dir / 'spine.py')

# Visualizer (depends on spine)
load_module('visualizer', evez_dir / 'visualizer.py')

# Pattern engine (depends on quantum_rng, spine)
load_module('pattern_engine', evez_dir / 'pattern_engine.py')

# Coherency sync (depends on quantum_rng, spine)
load_module('coherency_sync', evez_dir / 'coherency_sync.py')

# Cognition wheel (depends on quantum_rng, spine)
load_module('cognition_wheel', evez_dir / 'cognition_wheel.py')

# FSC (depends on quantum_rng, spine)
load_module('fsc', evez_dir / 'fsc.py')

# Threat engine (depends on quantum_rng, spine)
load_module('threat_engine', evez_dir / 'threat_engine.py')

# Rollback engine (depends on quantum_rng, spine)
load_module('rollback_engine', evez_dir / 'rollback_engine.py')

# Play forever (depends on quantum_rng, spine, fsc)
load_module('play_forever', evez_dir / 'play_forever.py')

# Truth sifter (depends on quantum_rng, spine)
load_module('truth_sifter', evez_dir / 'truth_sifter.py')

# Self building (depends on quantum_rng, spine, cognition_wheel)
load_module('self_building', evez_dir / 'self_building.py')

# Psyops (depends on quantum_rng, spine, truth_sifter)
load_module('psyops', evez_dir / 'psyops.py')

# EVEZ voice (depends on quantum_rng)
load_module('evez_voice', evez_dir / 'evez_voice.py')

# Main (depends on everything)
main_module = load_module('main', evez_dir / 'main.py')

print("[Launcher] All modules loaded successfully!")
print()

# Run the game
if __name__ == "__main__":
    main_module.main()
