"""
evezos — EVEZ-OS canonical Python package
Author: Steven Crawford-Maggard (EVEZ666)

Entry point for all EVEZ-OS subsystems.
Import surface:
  from evezos import EVEZCore, EVEZFork
  from evezos.fire import FireEngine
  from evezos.cognition import CognitionLayer
  from evezos.bridge import EventBridge
  from evezos.mrom import MROMCartridge
"""

from evezos.core import EVEZCore, EVEZFork
from evezos.fire import FireEngine
from evezos.cognition import CognitionLayer
from evezos.bridge import EventBridge
from evezos.mrom import MROMCartridge

__version__ = "3.1.0"
__all__ = [
    "EVEZCore", "EVEZFork",
    "FireEngine",
    "CognitionLayer",
    "EventBridge",
    "MROMCartridge",
]
