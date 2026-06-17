"""
evezos/fire — FireEngine: unified cycle runner for all ordinals (1st–7th)

Replaces 24 root-level fire_*.py files:
  fire_approach, fire_border, fire_horizon, fire_intensify,
  fire_peak_approach, fire_rekindle_watch, fire_rekindle_watch_2,
  fire_resonance_proof, fire_settling, fire_sustain,
  pre_fire_protocol, post_fire_analysis, post_border_analysis,
  post_settling, third_fire, fourth_fire_analysis, fourth_fire_trigger,
  post_fourth_fire, post_fourth_fire_2, fifth_fire, sixth_fire,
  sixth_fire_approach, seventh_fire_ignition, ceiling_zone
"""

from evezos.fire.engine import FireEngine, FireCycle, FirePhase
__all__ = ["FireEngine", "FireCycle", "FirePhase"]
