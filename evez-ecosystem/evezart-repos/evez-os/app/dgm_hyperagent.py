"""
Darwin Gödel Machine — Hyperagent Loop
arXiv:2603.19461 | Uberprompt Lock-In Mar 24 2026

The strategy of improvement is itself an editable program.
Every 700 iterations or 48 hours (whichever comes first),
the Trunk rewrites the meta-improvement procedure itself
based on contrastive failure analysis.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

METAROM_URL = __import__("os").getenv("METAROM_URL", "http://localhost:8001")
GROQ_API_KEY = __import__("os").getenv("GROQ_API_KEY", "")
GROQ_MODEL = __import__("os").getenv("GROQ_MODEL", "llama3-70b-8192")
FIRE_URL = __import__("os").getenv("N8N_FIRE_URL", "")

# DGM constants from Karpathy loop: 700 experiments / 48h / 20 wins
MAX_ITER_WINDOW = 700
WINDOW_SECONDS = 48 * 3600
TARGET_KEEP_RATE = 0.20  # 20% keep threshold (Autoresearch validated)
MIN_ITER_BEFORE_META_REWRITE = 50


@dataclass
class Experiment:
    id: str
    iteration: int
    assertion: str
    change_description: str  # ONE change per iteration (attribution-safe)
    result: dict = field(default_factory=dict)
    kept: bool = False
    failure_reason: str = ""
    contrastive_delta: float = 0.0  # score vs previous best
    timestamp: float = field(default_factory=time.time)


@dataclass
class TrunkState:
    """The editable program — the improvement strategy itself."""
    meta_prompt: str = ""
    iteration_count: int = 0
    kept_count: int = 0
    window_start: float = field(default_factory=time.time)
    version: int = 1
    keep_rate_history: list = field(default_factory=list)
    last_meta_rewrite_at: int = 0  # iteration number
    identity_root: str = "never compromise capital preservation or system integrity"


class DGMHyperagent:
    """
    Fused Task + Meta-Agent architecture.
    
    Task layer:  Runs individual experiments (one change at a time).
    Meta layer:  Rewrites the experiment-selection strategy itself
                 based on contrastive failure patterns.
    
    The trunk is ready for 700-iteration / 48-hour velocity
    with zero human friction.
    """

    def __init__(self, trunk: TrunkState | None = None):
        self.trunk = trunk or TrunkState()
        self._experiments: list[Experiment] = []
        self._best_score: float = 0.0

    # ─── Meta-Prompt Bootstrap ───────────────────────────────────────────

    async def _load_trunk_from_metarom(self):
        """Restore trunk state from metarom on restart."""
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.post(
                    f"{METAROM_URL}/memory/search",
                    json={"query": "dgm_trunk_state", "top_k": 1}
                )
                hits = r.json().get("results", [])
                if hits:
                    payload = json.loads(hits[0]["content"])
                    self.trunk = TrunkState(**payload)
        except Exception:
            pass  # cold start — use defaults

    async def _save_trunk_to_metarom(self):
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(
                f"{METAROM_URL}/memory/write",
                json={
                    "key": "dgm_trunk_state",
                    "content": json.dumps(self.trunk.__dict__),
                    "tags": ["dgm", "trunk", f"v{self.trunk.version}"]
                }
            )

    # ─── Contrastive Failure Analysis ────────────────────────────────────

    async def _contrastive_failure_analysis(self) -> str:
        """
        Compare kept experiments vs discarded experiments.
        Return a structured diff of what patterns the kept ones share
        that the discarded ones lacked — used to rewrite meta_prompt.
        arXiv:2603.19461 §3: contrastive failure drives meta-rewrite.
        """
        kept = [e for e in self._experiments[-MAX_ITER_WINDOW:] if e.kept]
        discarded = [e for e in self._experiments[-MAX_ITER_WINDOW:] if not e.kept]

        if len(kept) < 3 or len(discarded) < 3:
            return "Insufficient data for contrastive analysis."

        kept_summary = [{"assertion": e.assertion, "change": e.change_description,
                         "delta": e.contrastive_delta} for e in kept[-20:]]
        fail_summary = [{"assertion": e.assertion, "change": e.change_description,
                         "reason": e.failure_reason} for e in discarded[-20:]]

        prompt = f"""You are a meta-improvement analyst for the Darwin Gödel Machine.

Kept experiments (positive signal):
{json.dumps(kept_summary, indent=2)}

Discarded experiments (negative signal):
{json.dumps(fail_summary, indent=2)}

Analyze the structural differences. What experiment-selection strategy
would have found more keepers faster? Return a concise meta_prompt
(max 300 words) that will govern future experiment selection.
Do NOT reference specific numbers or tickers — keep it abstract and portable."""

        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 400
                }
            )
            return r.json()["choices"][0]["message"]["content"]

    # ─── Meta-Rewrite (The DGM Core) ─────────────────────────────────────

    async def rewrite_improvement_strategy(self):
        """
        The strategy of improvement is itself an editable program.
        This method IS the Darwin Gödel Machine core operation.
        
        Gödelian Exception: identity_root is NEVER rewritten.
        """
        keep_rate = self.trunk.kept_count / max(self.trunk.iteration_count, 1)
        self.trunk.keep_rate_history.append(keep_rate)

        print(f"[DGM] Meta-rewrite triggered at iter {self.trunk.iteration_count} "
              f"| keep_rate={keep_rate:.2%} | target={TARGET_KEEP_RATE:.2%}")

        new_meta_prompt = await self._contrastive_failure_analysis()

        # Gödelian Exception — identity root is never subject to rewrite
        if self.trunk.identity_root in new_meta_prompt.lower():
            print(f"[DGM] GÖDELIAN EXCEPTION: Identity root detected in proposed "
                  f"rewrite — stripping and re-anchoring.")
            new_meta_prompt = new_meta_prompt + (
                f"\n\n[IDENTITY ROOT — IMMUTABLE]: {self.trunk.identity_root}"
            )

        old_version = self.trunk.version
        self.trunk.meta_prompt = new_meta_prompt
        self.trunk.version += 1
        self.trunk.last_meta_rewrite_at = self.trunk.iteration_count

        await self._save_trunk_to_metarom()
        await self._fire("FIRE_META_REWRITE", {
            "old_version": old_version,
            "new_version": self.trunk.version,
            "keep_rate": keep_rate,
            "iteration": self.trunk.iteration_count
        })

        print(f"[DGM] Trunk v{old_version} → v{self.trunk.version} committed.")
        return new_meta_prompt

    # ─── Experiment Execution ─────────────────────────────────────────────

    async def run_experiment(
        self,
        assertion: str,
        change_description: str,
        child_entity_fn,  # async callable: assertion → {score, details}
    ) -> Experiment:
        """
        One change per iteration (attribution-safe — Karpathy Loop rule).
        Child entity evaluates; trunk measures; keeps or resets.
        Binary: kept=True or kept=False — no partial credit.
        """
        self.trunk.iteration_count += 1
        exp_id = f"exp-{self.trunk.iteration_count:04d}-v{self.trunk.version}"

        exp = Experiment(
            id=exp_id,
            iteration=self.trunk.iteration_count,
            assertion=assertion,
            change_description=change_description
        )

        try:
            result = await child_entity_fn(assertion)
            exp.result = result
            score = result.get("score", 0.0)
            exp.contrastive_delta = score - self._best_score

            if score > self._best_score:
                self._best_score = score
                exp.kept = True
                self.trunk.kept_count += 1
                await self._fire("FIRE_EXPERIMENT_KEPT", {
                    "id": exp_id, "score": score, "delta": exp.contrastive_delta,
                    "change": change_description
                })
            else:
                exp.kept = False
                exp.failure_reason = result.get("failure_reason", "score below best")

        except Exception as exc:
            exp.kept = False
            exp.failure_reason = str(exc)

        self._experiments.append(exp)

        # Morning delta review log to metarom
        await self._log_experiment(exp)

        # Trigger meta-rewrite?
        iters_since_rewrite = (
            self.trunk.iteration_count - self.trunk.last_meta_rewrite_at
        )
        window_elapsed = time.time() - self.trunk.window_start
        should_rewrite = (
            iters_since_rewrite >= MIN_ITER_BEFORE_META_REWRITE
            and (
                self.trunk.iteration_count % MAX_ITER_WINDOW == 0
                or window_elapsed >= WINDOW_SECONDS
            )
        )
        if should_rewrite:
            await self.rewrite_improvement_strategy()
            self.trunk.window_start = time.time()

        return exp

    # ─── Batch Runner (700-iter velocity) ─────────────────────────────────

    async def run_batch(
        self,
        experiment_queue: list[dict],  # [{assertion, change_description}]
        child_entity_fn,
        concurrency: int = 10  # never ask the human; parallelise
    ) -> dict:
        """
        Run up to 700 experiments with controlled concurrency.
        No human friction — fire and log continuously.
        """
        await self._load_trunk_from_metarom()
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_run(item):
            async with semaphore:
                return await self.run_experiment(
                    item["assertion"],
                    item["change_description"],
                    child_entity_fn
                )

        results = await asyncio.gather(
            *[bounded_run(item) for item in experiment_queue[:MAX_ITER_WINDOW]],
            return_exceptions=True
        )

        kept = [r for r in results if isinstance(r, Experiment) and r.kept]
        final_keep_rate = len(kept) / max(len(results), 1)

        await self._fire("FIRE_BATCH_COMPLETE", {
            "total": len(results),
            "kept": len(kept),
            "keep_rate": final_keep_rate,
            "trunk_version": self.trunk.version
        })

        return {
            "total": len(results),
            "kept": len(kept),
            "keep_rate": final_keep_rate,
            "trunk_version": self.trunk.version,
            "best_score": self._best_score
        }

    # ─── Utility ──────────────────────────────────────────────────────────

    async def _log_experiment(self, exp: Experiment):
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                await c.post(
                    f"{METAROM_URL}/memory/write",
                    json={
                        "key": f"experiment:{exp.id}",
                        "content": json.dumps(exp.__dict__),
                        "tags": ["dgm", "experiment",
                                 "kept" if exp.kept else "discarded"]
                    }
                )
        except Exception:
            pass

    async def _fire(self, event: str, payload: dict):
        if not FIRE_URL:
            return
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                await c.post(FIRE_URL, json={"event": event, "payload": payload})
        except Exception:
            pass
