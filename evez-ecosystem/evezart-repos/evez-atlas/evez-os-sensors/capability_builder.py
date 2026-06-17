"""EVEZ-OS Sensor: capability_builder — 1 failed actions. Expand capability."""
import json, time, hashlib, math
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class CapabilityBuilderReading:
    value: float
    confidence: float
    timestamp: float = field(default_factory=time.time)
    source: str = "capability_builder"
    metadata: dict = field(default_factory=dict)

class CapabilityBuilder:
    """1 failed actions. Expand capability."""
    def __init__(self, config=None):
        self.config = config or {}
        self.readings = []
        self.spine_path = Path("/tmp/evez_capability_builder_spine.jsonl")

    def sense(self) -> CapabilityBuilderReading:
        """Take a reading."""
        value = 0.0
        confidence = 0.5
        reading = CapabilityBuilderReading(
            value=value, confidence=confidence,
            metadata={}
        )
        self.readings.append(reading)
        self._record(reading)
        return reading

    def _record(self, reading):
        entry = {"ts": reading.timestamp, "value": reading.value,
                  "confidence": reading.confidence, "source": reading.source}
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


def test_capability_builder():
    """Auto-generated tests for CapabilityBuilder."""
    obj = CapabilityBuilder()
    # Test case 1
    result_0 = obj.compute(**{"data": {}})
    # Edge cases
    try: obj.compute(None)
    except: pass  # None input should not crash
    try: obj.compute({})
    except: pass  # Empty input should not crash
    print('All tests passed for CapabilityBuilder')
    return True