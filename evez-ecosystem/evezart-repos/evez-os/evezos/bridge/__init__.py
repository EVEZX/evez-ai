"""
evezos/bridge — EventBridge

Bi-directional event channel:
  evez-agentnet AgentMemory.write() → FIRE events → evez-os spine
  spine → topology updates → evez-meme-bus → income signals → MetaLearner

Zero-cost deployment on Railway free tier.
Persistence: append-only JSONL (no DB required).
"""

from evezos.bridge.event_bridge import EventBridge, BridgeEvent, EventType
__all__ = ["EventBridge", "BridgeEvent", "EventType"]
