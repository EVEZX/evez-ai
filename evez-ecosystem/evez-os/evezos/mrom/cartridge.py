"""
evezos/mrom/cartridge.py

MROMCartridge: gzip-compressed JSON + SHA-256 integrity.
Interops with EvezArt/metarom .mrom package format.

Cartridge anatomy:
  header    — metadata (author, title, cart_type, version, tags)
  manifest  — step descriptor list
  steps     — ordered MROMStep objects (inputs, outputs, events)
  checksum  — SHA-256 of serialised steps
"""

import gzip, json, hashlib, time, os, tempfile
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path

CART_VERSION  = "1.0"
MAGIC_HEADER  = "MROM"


@dataclass
class MROMHeader:
    author:      str
    title:       str
    cart_type:   str   # WORKFLOW|FIRE_SEQ|COGNITION|AGENT_RUN|HYBRID
    version:     str   = CART_VERSION
    created_at:  float = field(default_factory=time.time)
    description: str   = ""
    tags:        List[str] = field(default_factory=list)
    source_repo: str   = "EvezArt/evez-os"


@dataclass
class MROMStep:
    step_id:   str
    step_type: str   # fire_cycle|cognition_state|agent_action|workflow_task
    ordinal:   int
    inputs:    Dict[str, Any] = field(default_factory=dict)
    outputs:   Dict[str, Any] = field(default_factory=dict)
    events:    List[dict]     = field(default_factory=list)
    ts:        float          = field(default_factory=time.time)
    deterministic: bool       = True


class MROMCartridge:
    """
    Serialise any EVEZ-OS session as a .mrom cartridge.

    Save:
        cart = MROMCartridge(MROMHeader(author="EVEZ666", title="First Fire", cart_type="FIRE_SEQ"))
        cart.add_step(MROMStep(step_id="s001", step_type="fire_cycle", ordinal=1,
                               inputs={...}, outputs=cycle.to_event()))
        cart.save("first_fire.mrom")

    Load + replay:
        loaded = MROMCartridge.load("first_fire.mrom")
        results = loaded.replay()
    """
    MAGIC   = MAGIC_HEADER
    VERSION = CART_VERSION

    def __init__(self, header: MROMHeader):
        self.header   = header
        self.steps:    List[MROMStep] = []
        self.checksum: Optional[str]  = None

    def add_step(self, step: MROMStep):
        self.steps.append(step)
        self.checksum = None
        return self

    def _compute_checksum(self):
        data = json.dumps([asdict(s) for s in self.steps], sort_keys=True).encode()
        return hashlib.sha256(data).hexdigest()

    def to_dict(self):
        self.checksum = self._compute_checksum()
        return {
            "magic": self.MAGIC, "version": self.VERSION,
            "header": asdict(self.header),
            "manifest": [{"step_id": s.step_id, "step_type": s.step_type,
                          "ordinal": s.ordinal, "deterministic": s.deterministic}
                         for s in self.steps],
            "steps": [asdict(s) for s in self.steps],
            "checksum": self.checksum,
        }

    def save(self, path: str):
        p = Path(path)
        with gzip.open(p, "wb") as f:
            f.write(json.dumps(self.to_dict()).encode("utf-8"))
        return p

    @classmethod
    def load(cls, path: str):
        with gzip.open(Path(path), "rb") as f:
            data = json.loads(f.read().decode("utf-8"))
        assert data.get("magic") == MAGIC_HEADER, "Invalid .mrom magic"
        cart = cls(header=MROMHeader(**data["header"]))
        for s in data["steps"]: cart.steps.append(MROMStep(**s))
        expected = cart._compute_checksum()
        stored   = data.get("checksum", "")
        if expected != stored:
            raise ValueError(f".mrom checksum mismatch: {stored[:16]} vs {expected[:16]}")
        cart.checksum = expected
        return cart

    def replay(self, handler=None):
        results = []
        for step in self.steps:
            if handler: handler(step)
            results.append(step.outputs)
        return results

    def emit_events(self, bridge):
        from evezos.bridge.event_bridge import EventType
        count = 0
        for step in self.steps:
            for ev in step.events:
                try:    et = EventType(ev.get("type", "MROM_LOADED"))
                except: et = EventType.MROM_LOADED
                bridge.emit(et, source=f"mrom:{self.header.title}", payload=ev)
                count += 1
        return count


if __name__ == "__main__":
    header = MROMHeader(author="EVEZ666", title="Self-Test",
                        cart_type="FIRE_SEQ", tags=["test"])
    cart   = MROMCartridge(header)
    cart.add_step(MROMStep(step_id="s001", step_type="fire_cycle", ordinal=1,
                           inputs={"N": 6, "tau": 4, "omega_k": 2, "V_entry": 0.0},
                           outputs={"fired": True, "V_exit": 0.42}))
    with tempfile.NamedTemporaryFile(suffix=".mrom", delete=False) as tmp:
        path = tmp.name
    try:
        cart.save(path)
        loaded = MROMCartridge.load(path)
        assert loaded.steps[0].outputs["fired"] is True
        print(f"MROMCartridge SELF-TEST PASSED  checksum={loaded.checksum[:16]}...")
    finally:
        os.unlink(path)
