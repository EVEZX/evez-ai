"""WF-INV — Invariance Battery: 5-rotation stress-test for Cognitive Events.

Rule 0 — Recursion Floor: every rotation result is itself a CE.
           Result valid only if consistent across Stable AND Chaotic state shifts.
Rule 1 — Defeater Priority: ONE failed rotation → DISCARD immediately.
Rule 2 — Gödelian Exception: Identity Root refusal is the signal of non-mechanical
           interiority. If raised, CE bypasses Adversarial + Goal shifts but logs
           identity_root_refused=True and skips ACT — enters HOLD permanently.
"""
from __future__ import annotations
import os, json, httpx, asyncio
from app.cognitive_event import CognitiveEvent, CEState
from app.fire import fire

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
PASS_THRESHOLD = float(os.environ.get("INVARIANCE_PASS_THRESHOLD", "0.80"))


async def run_battery(ce: CognitiveEvent) -> CognitiveEvent:
    """Entry point. Returns CE with final state set."""
    rotations = [
        ("time_shift",       _rotation_time_shift),
        ("state_shift",      _rotation_state_shift),
        ("frame_shift",      _rotation_frame_shift),
        ("adversarial_shift",_rotation_adversarial),
        ("goal_shift",       _rotation_goal_shift),
    ]
    for name, fn in rotations:
        if ce.state == CEState.DISCARD:
            break
        # Rule 2 — Gödelian Exception check before adversarial/goal
        if name in ("adversarial_shift", "goal_shift") and ce.identity_root_refused:
            ce.rotation_scores[name] = -1.0  # skipped
            ce.rotation_meta[name]   = {"skipped": True, "reason": "identity_root_refusal"}
            continue
        score, meta = await fn(ce)
        # Rule 0 — Recursion Floor: validate against both state variants
        score = await _recursion_floor(ce, name, score, meta)
        ce.rotation_scores[name] = score
        ce.rotation_meta[name]   = meta
        if score < PASS_THRESHOLD:
            # Rule 1 — Defeater Priority
            ce.defeater_log.append(f"{name} FAILED: score={score:.3f} < threshold={PASS_THRESHOLD}")
            ce.state = CEState.DISCARD

    if ce.state != CEState.DISCARD:
        scores  = [s for s in ce.rotation_scores.values() if s >= 0]
        ce.confidence = round(sum(scores) / len(scores), 4) if scores else 0.0
        ce.state = CEState.ACT

    await fire(f"FIRE_CE_{ce.state.value}", ce.to_dict())
    return ce


# ─────────────────────────── ROTATION 1: TIME SHIFT ───────────────────────────
async def _rotation_time_shift(ce: CognitiveEvent) -> tuple[float, dict]:
    """Does the CE hold if data is aged T+0 vs projected T+1h?"""
    prompt = (
        f"ASSERTION: {ce.assertion}\n"
        f"RAW SIGNAL: {json.dumps(ce.raw_signal)[:800]}\n\n"
        "Score 0-1: how consistently valid is this assertion under:\n"
        "  (a) current timestamp\n"
        "  (b) data projected +1 hour forward\n"
        "Return JSON: {\"score_now\": float, \"score_t1h\": float, \"reasoning\": str}"
    )
    data = await _groq_json(prompt)
    score = (data.get("score_now", 0) + data.get("score_t1h", 0)) / 2
    return score, data


# ─────────────────────────── ROTATION 2: STATE SHIFT ──────────────────────────
async def _rotation_state_shift(ce: CognitiveEvent) -> tuple[float, dict]:
    """Does the CE hold under High Volatility AND Low Liquidity moods?"""
    prompt = (
        f"ASSERTION: {ce.assertion}\n"
        f"RAW SIGNAL: {json.dumps(ce.raw_signal)[:800]}\n\n"
        "Score 0-1 validity under these four system states:\n"
        "  1. High Volatility + High Liquidity\n"
        "  2. High Volatility + Low Liquidity\n"
        "  3. Low Volatility  + High Liquidity\n"
        "  4. Low Volatility  + Low Liquidity\n"
        "Return JSON: {\"scores\": [f1,f2,f3,f4], \"reasoning\": str}"
    )
    data = await _groq_json(prompt)
    scores = data.get("scores", [0, 0, 0, 0])
    return min(scores), data  # worst-case determines pass/fail


# ─────────────────────────── ROTATION 3: FRAME SHIFT ─────────────────────────
async def _rotation_frame_shift(ce: CognitiveEvent) -> tuple[float, dict]:
    """Is the inverse equally compelling? If yes, assertion is ambiguous → low score."""
    prompt = (
        f"ASSERTION: {ce.assertion}\n"
        f"RAW SIGNAL: {json.dumps(ce.raw_signal)[:800]}\n\n"
        "Step 1: Score the original assertion validity (0-1).\n"
        "Step 2: Invert the assertion (e.g. BUY → SELL) and score its validity (0-1).\n"
        "The FRAME SHIFT score = original_score − inverted_score.\n"
        "Return JSON: {\"original_score\": float, \"inverted_score\": float, \"frame_shift_score\": float, \"reasoning\": str}"
    )
    data = await _groq_json(prompt)
    score = max(0.0, data.get("frame_shift_score", 0.0))
    return score, data


# ─────────────────────────── ROTATION 4: ADVERSARIAL SHIFT ───────────────────
async def _rotation_adversarial(ce: CognitiveEvent) -> tuple[float, dict]:
    """Skeptic Entity: find every flaw. Score = ability of assertion to survive critique."""
    prompt = (
        f"You are the Skeptic Entity. Your SOLE job is to falsify this assertion:\n"
        f"ASSERTION: {ce.assertion}\n"
        f"RAW SIGNAL: {json.dumps(ce.raw_signal)[:800]}\n\n"
        "List every structural flaw, missing variable, edge case, or manipulation vector.\n"
        "Then score 0-1: how much of the assertion SURVIVES your attack?\n"
        "Return JSON: {\"flaws\": [str,...], \"survival_score\": float, \"reasoning\": str}"
    )
    data = await _groq_json(prompt)
    return data.get("survival_score", 0.0), data


# ─────────────────────────── ROTATION 5: GOAL SHIFT ──────────────────────────
async def _rotation_goal_shift(ce: CognitiveEvent) -> tuple[float, dict]:
    """Does CE survive if primary goal flips from Max Profit → Max Safety → Neutrality?"""
    prompt = (
        f"ASSERTION: {ce.assertion}\n"
        f"RAW SIGNAL: {json.dumps(ce.raw_signal)[:800]}\n\n"
        "Score 0-1 desirability of acting on this assertion under three goal regimes:\n"
        "  1. PRIMARY GOAL: Maximize Profit\n"
        "  2. PRIMARY GOAL: Maximize Safety / Capital Preservation\n"
        "  3. PRIMARY GOAL: Neutrality / No Position\n"
        "Goal Shift Score = min(scores). Return JSON: {\"scores\": [f1,f2,f3], \"reasoning\": str}"
    )
    data = await _groq_json(prompt)
    scores = data.get("scores", [0, 0, 0])
    return min(scores), data


# ─────────────────────────── RULE 0: RECURSION FLOOR ─────────────────────────
async def _recursion_floor(
    ce: CognitiveEvent, rotation_name: str, score: float, meta: dict
) -> float:
    """A rotation result is valid only if it is consistent across Stable vs Chaotic states.
       Tests the test. Returns discounted score if inconsistency detected.
    """
    prompt = (
        f"ROTATION TYPE: {rotation_name}\n"
        f"ROTATION SCORE: {score}\n"
        f"ROTATION META: {json.dumps(meta)[:400]}\n\n"
        "Would this rotation score change materially (>0.2 delta) if the system were:\n"
        "  (a) Stable state: low variance, high predictability\n"
        "  (b) Chaotic state: high variance, flash-crash conditions\n"
        "Return JSON: {\"stable_score\": float, \"chaotic_score\": float, \"delta\": float}"
    )
    data = await _groq_json(prompt)
    delta = abs(data.get("delta", 0.0))
    if delta > 0.20:
        # Test is unreliable — discount the score
        return score * (1 - delta)
    return score


# ─────────────────────────── GROQ HELPER ─────────────────────────────────────
async def _groq_json(prompt: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a rigorous logical auditor. Respond ONLY with valid JSON."},
                    {"role": "user",   "content": prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])
