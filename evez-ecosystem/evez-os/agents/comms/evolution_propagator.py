from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.comms.agentspeak import AgentSpeakMessage, MessageType, encode_message


@dataclass
class EvolutionPropagator:
    sent: dict[str, set[str]] = field(default_factory=dict)
    adopted: dict[str, set[str]] = field(default_factory=dict)
    species_events: list[dict[str, Any]] = field(default_factory=list)

    def track_sent(self, improvement_id: str, peer_id: str) -> None:
        self.sent.setdefault(improvement_id, set()).add(peer_id)

    def track_adopted(self, improvement_id: str, peer_id: str) -> float:
        self.adopted.setdefault(improvement_id, set()).add(peer_id)
        sent_count = max(len(self.sent.get(improvement_id, set())), 1)
        rate = len(self.adopted[improvement_id]) / sent_count
        if rate > 0.75:
            self.species_events.append(
                {
                    "event": "species_level_evolution",
                    "improvement_id": improvement_id,
                    "adoption_rate": rate,
                }
            )
        return rate

    def build_broadcast(self, sender_node_id: str, improvement_id: str, diff: dict[str, Any], ts_ns: int) -> bytes:
        msg = AgentSpeakMessage(
            msg_type=MessageType.EVOLUTION_BROADCAST,
            sender_node_id=sender_node_id,
            recipient_node_id="*",
            timestamp_ns=ts_ns,
            payload={"improvement_id": improvement_id, "diff": diff},
        )
        return encode_message(msg)
