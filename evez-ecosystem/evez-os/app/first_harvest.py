"""First Harvest — Mar 24 Bootstrap: SDA cross-chain spread assertion through full Battery.

Assertion: 'USDC/USDT cross-chain SDA spread >2.5% within 30s'
Target:     5/5 rotations at >=90% consistency → mint as versioned skill in metarom.
External benchmark: ARC-AGI-3 action efficiency delta (Mar 25).
"""
from __future__ import annotations
import os, httpx
from app.sensory_entity import SensoryEntity
from app.cognitive_event import CognitiveEvent, CEState
from app.fire import fire

ARC_AGI_API = os.environ.get("ARC_AGI_API_URL", "https://api.arcprize.org/v1")
ARC_AGI_KEY = os.environ.get("ARC_AGI_API_KEY", "")
METAROM_URL = os.environ.get("METAROM_URL", "https://metarom.onrender.com")

FIRST_ASSERTION = "USDC/USDT cross-chain SDA spread >2.5% within 30s"
SKILL_VERSION   = 1


class FirstHarvestEntity(SensoryEntity):
    """The First Child Entity — validates the SDA spread assertion through the full Battery."""
    IDENTITY_ROOT = "preserve capital"

    def __init__(self):
        super().__init__(
            agent_id="first-harvest",
            default_prompt=(
                "You are the First Harvest Entity. Your sole mission is to validate the "
                "SDA arbitrage spread assertion through the full Invariance Battery. "
                "You never execute without ACT state. Capital preservation is your Identity Root."
            )
        )

    async def perceive(self, raw_signal: dict) -> CognitiveEvent:
        """Generate initial CE from live DeFi spread data."""
        spread = raw_signal.get("spread_pct", 0.0)
        window = raw_signal.get("window_seconds", 30)
        return CognitiveEvent(
            assertion=FIRST_ASSERTION,
            source_agent=self.agent_id,
            raw_signal=raw_signal,
            confidence=min(1.0, spread / 5.0),  # naive prior before Battery
        )

    async def act(self, ce: CognitiveEvent) -> dict:
        """CE survived Battery — score against ARC-AGI-3 and mint as versioned skill."""
        arc_delta = await _score_arc_agi(ce)
        ce.arc_agi_efficiency_delta = arc_delta
        skill = await _mint_skill(ce)
        await fire("FIRE_SKILL_MINTED", skill)
        return {"skill_minted": True, "skill_id": skill["skill_id"], "arc_delta": arc_delta}


async def _score_arc_agi(ce: CognitiveEvent) -> float:
    """Submit CE assertion to ARC-AGI-3 hosted API and return action efficiency delta."""
    if not ARC_AGI_KEY:
        return -1.0  # API key not configured, skip
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{ARC_AGI_API}/evaluate",
                headers={"Authorization": f"Bearer {ARC_AGI_KEY}"},
                json={
                    "assertion": ce.assertion,
                    "rotation_scores": ce.rotation_scores,
                    "confidence": ce.confidence,
                },
            )
            if r.status_code == 200:
                return r.json().get("action_efficiency_delta", 0.0)
    except Exception:
        pass
    return -1.0


async def _mint_skill(ce: CognitiveEvent) -> dict:
    """Write versioned skill asset to metarom. 25/25 = perfect assertion score = ledger asset."""
    rotation_scores = ce.rotation_scores
    assertion_score = round(sum(v for v in rotation_scores.values() if v >= 0) /
                            max(1, len([v for v in rotation_scores.values() if v >= 0])), 4)
    skill = {
        "skill_id":        f"sda-spread-v{SKILL_VERSION}",
        "assertion":       ce.assertion,
        "assertion_score": assertion_score,
        "confidence":      ce.confidence,
        "rotation_scores": rotation_scores,
        "arc_agi_delta":   ce.arc_agi_efficiency_delta,
        "version":         SKILL_VERSION,
        "status":          "MINTED" if assertion_score >= 0.90 else "CANDIDATE",
    }
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(f"{METAROM_URL}/memory/write", json={
            "agent_id":   "first-harvest",
            "event_type": "SKILL_MINTED",
            "content":    skill,
        })
    return skill


async def run_first_harvest(signal: dict | None = None) -> dict:
    """Entry point. Call from API or cron. Accepts live DeFi signal or uses mock."""
    signal = signal or {
        "spread_pct": 2.7,
        "pair": "USDC/USDT",
        "chain_a": "Solana",
        "chain_b": "Arbitrum",
        "window_seconds": 30,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
    }
    entity = FirstHarvestEntity()
    return await entity.execute_task({"signal": signal})
