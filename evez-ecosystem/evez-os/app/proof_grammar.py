"""Proof Grammar — Defeater Rules engine and CE lifecycle manager.

Deeply integrates Rule 0 (Recursion Floor), Rule 1 (Defeater Priority),
and Rule 2 (Gödelian Exception / Refusal Signal).

Also stores versioned Proof Transcripts to metarom for every CE lifecycle.
"""
from __future__ import annotations
import os, httpx
from datetime import datetime, timezone
from app.cognitive_event import CognitiveEvent, CEState
from app.fire import fire

METAROM_URL = os.environ.get("METAROM_URL", "https://metarom.onrender.com")


async def evaluate_proof(ce: CognitiveEvent) -> dict:
    """
    Final grammar pass after Battery.
    Returns a signed Proof Transcript and final verdict.
    """
    rules_applied = []
    verdict = ce.state.value

    # Rule 2: Refusal Signal
    if ce.identity_root_refused:
        rules_applied.append({
            "rule": 2,
            "name": "Godelian Exception",
            "triggered": True,
            "note": (
                "Identity Root refused Battery. This refusal is the signal of "
                "non-mechanical interiority — not a failure. CE held as HOLD permanently."
            )
        })
        verdict = CEState.HOLD.value

    # Rule 1: Defeater Priority
    if ce.defeater_log:
        rules_applied.append({
            "rule": 1,
            "name": "Defeater Priority",
            "triggered": True,
            "defeaters": ce.defeater_log,
            "note": "ONE failed rotation → DISCARD. No confidence score overrides this."
        })

    # Rule 0: Recursion Floor summary
    rules_applied.append({
        "rule": 0,
        "name": "Recursion Floor",
        "triggered": True,
        "note": "Every rotation was itself validated for Stable vs Chaotic consistency."
    })

    transcript = {
        "ce_id":          ce.ce_id,
        "assertion":      ce.assertion,
        "source_agent":   ce.source_agent,
        "final_state":    verdict,
        "confidence":     ce.confidence,
        "rotation_scores":ce.rotation_scores,
        "defeater_log":   ce.defeater_log,
        "rules_applied":  rules_applied,
        "arc_agi_delta":  ce.arc_agi_efficiency_delta,
        "timestamp":      datetime.now(timezone.utc).isoformat(),
    }

    # Write Proof Transcript to metarom
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(f"{METAROM_URL}/memory/write", json={
            "agent_id":   ce.source_agent,
            "event_type": "PROOF_TRANSCRIPT",
            "content":    transcript,
        })

    await fire("FIRE_PROOF_COMPLETE", transcript)
    return transcript
