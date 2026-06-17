"""
evezos/mrom — MROMCartridge

SureThing / agentnet / FireEngine sessions serialised as .mrom files.
Distributable, deterministically replayable, zero cloud dependency.
Interops with EvezArt/metarom arcade cart loader.

Formats:
  WORKFLOW   — SureThing/surething-offline workflow replay
  FIRE_SEQ   — FireEngine cycle sequence
  COGNITION  — CognitionLayer CV sequence
  AGENT_RUN  — evez-agentnet session
  HYBRID     — mixed type
"""

from evezos.mrom.cartridge import MROMCartridge, MROMHeader, MROMStep
__all__ = ["MROMCartridge", "MROMHeader", "MROMStep"]
