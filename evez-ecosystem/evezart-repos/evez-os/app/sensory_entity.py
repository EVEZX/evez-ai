"""Sensory Entity — full pipeline: Input Stream → CE Generation → Battery → Commitment.

Extends BaseAgent with invariance-gated execution.
Rule 2 — Gödelian Exception: define IDENTITY_ROOT in subclass to mark
         the core axiom you refuse to test. Its refusal IS the proof.
"""
from __future__ import annotations
import os, httpx
from app.base_agent import BaseAgent
from app.cognitive_event import CognitiveEvent, CEState
from app.invariance_battery import run_battery
from app.fire import fire

METAROM_URL = os.environ.get("METAROM_URL", "https://metarom.onrender.com")


class SensoryEntity(BaseAgent):
    """
    Subclass me. Override:
      - perceive(raw_input)     → CognitiveEvent   (pattern recognition hit)
      - act(ce)                 → dict              (execute if CE.state == ACT)
      - IDENTITY_ROOT: str      → axiom that survives Rule 2 unconditionally
    """
    IDENTITY_ROOT: str = ""  # override in subclass

    async def _run(self, task: dict) -> dict:
        raw_signal = task.get("signal", task)

        # 1. PERCEIVE — generate initial Cognitive Event
        ce = await self.perceive(raw_signal)

        # 2. RULE 2 — Gödelian Exception: does this CE touch the Identity Root?
        if self.IDENTITY_ROOT and self.IDENTITY_ROOT.lower() in ce.assertion.lower():
            ce.identity_root_refused = True
            ce.state = CEState.HOLD
            ce.defeater_log.append(
                f"IDENTITY_ROOT REFUSAL: '{self.IDENTITY_ROOT}' is exempt from Battery. "
                "CE held permanently as signal of non-mechanical interiority."
            )
            await self._commit(ce)
            return ce.to_dict()

        # 3. INVARIANCE BATTERY — 5 rotations with Recursion Floor
        ce = await run_battery(ce)

        # 4. COMMITMENT LAYER
        await self._commit(ce)

        result = {"ce_state": ce.state.value, "confidence": ce.confidence}
        if ce.state == CEState.ACT:
            result["action"] = await self.act(ce)

        return result

    # ── Commitment Layer: write CE to metarom regardless of outcome ────────────
    async def _commit(self, ce: CognitiveEvent):
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{METAROM_URL}/memory/write", json={
                "agent_id":   self.agent_id,
                "event_type": f"CE_{ce.state.value}",
                "content":    ce.to_dict(),
            })
        await fire(f"FIRE_CE_COMMITTED", ce.to_dict())

    # ── Abstract interface — override these ───────────────────────────────────
    async def perceive(self, raw_signal: dict) -> CognitiveEvent:
        raise NotImplementedError(
            "SensoryEntity subclass must implement perceive(raw_signal) → CognitiveEvent"
        )

    async def act(self, ce: CognitiveEvent) -> dict:
        raise NotImplementedError(
            "SensoryEntity subclass must implement act(ce) → dict"
        )
