"""Local Body Area Network (LBAN) digital twin."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CORE_PATH = [
    "identity_core",
    "consciousness_core",
    "memory",
    "survival_layer",
    "temporal_spine",
    "latency_pipeline",
]


@dataclass
class LocalLink:
    source: str
    target: str
    firing_rate_hz: float
    signal_strength: float
    myelination_factor: float
    use_count: int = 0


class LBANDigitalTwin:
    def __init__(self) -> None:
        self.links: dict[tuple[str, str], LocalLink] = {}
        for i in range(len(CORE_PATH) - 1):
            source, target = CORE_PATH[i], CORE_PATH[i + 1]
            self.links[(source, target)] = LocalLink(
                source=source,
                target=target,
                firing_rate_hz=35 + i * 5,
                signal_strength=0.65 + i * 0.05,
                myelination_factor=0.45 + i * 0.07,
            )

    def register_signal(self, source: str, target: str) -> LocalLink:
        link = self.links[(source, target)]
        link.use_count += 1
        link.firing_rate_hz += 0.5
        link.signal_strength = min(1.0, link.signal_strength + 0.01)
        link.myelination_factor = min(1.0, link.myelination_factor + 0.01)
        return link

    def export_state(self) -> dict[str, Any]:
        return {
            "api_path": "/api/network/lban",
            "links": [asdict(link) for link in self.links.values()],
        }
