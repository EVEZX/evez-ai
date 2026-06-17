"""
Trunk Runner — 700-Iteration Velocity Engine
No human friction. Morning delta review. Overnight gains.

Usage (from Render shell or cron):
  python -m app.trunk_runner --queue sda_spread --concurrency 10

Or via API:
  POST /api/trunk/run  {"queue": "sda_spread", "concurrency": 10}
"""

import asyncio
import json
import os
import time
from typing import Any

import httpx

from app.dgm_hyperagent import DGMHyperagent, TrunkState
from app.first_harvest import FirstHarvestEntity
from app.uberprompt import lock_uberprompt_to_terminal

FIRE_URL = os.getenv("N8N_FIRE_URL", "")
METAROM_URL = os.getenv("METAROM_URL", "http://localhost:8001")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Pre-built experiment queues keyed by name
EXPERIMENT_QUEUES: dict[str, list[dict]] = {
    "sda_spread": [
        # Vary the threshold, window, and chain pair — one change at a time
        {"assertion": f"USDC/USDT cross-chain SDA spread >{threshold}% within {window}s",
         "change_description": f"threshold={threshold}%, window={window}s"}
        for threshold in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        for window in [15, 20, 30, 45, 60]
    ],
    "arc_agi": [
        {"assertion": f"ARC-AGI-3 action efficiency delta > {delta} on environment class {env_class}",
         "change_description": f"efficiency_threshold={delta}, env_class={env_class}"}
        for delta in [0.05, 0.10, 0.15, 0.20, 0.25]
        for env_class in ["pattern", "spatial", "causal", "sequential"]
    ],
    "mev_latency": [
        {"assertion": f"Cross-chain MEV capture rate > {rate}% at <{latency}ms latency",
         "change_description": f"capture_rate_target={rate}%, latency_budget={latency}ms"}
        for rate in [50, 60, 70, 73]
        for latency in [10, 15, 20, 25]
    ]
}


class TrunkRunner:
    """Orchestrates the 700-iteration DGM velocity loop."""

    def __init__(self):
        self.system_prompt = lock_uberprompt_to_terminal("trunk")
        self.dgm = DGMHyperagent()
        self.harvester = FirstHarvestEntity()
        self.session_start = time.time()
        self.session_results: list[dict] = []

    async def _child_entity_fn(self, assertion: str) -> dict:
        """
        Child entity: runs Invariance Battery on the assertion,
        returns score + reasoning. Dissolves after returning.
        This is the 'Seed → Assert → Measure' step.
        """
        result = await self.harvester.run(signal={
            "assertion": assertion,
            "source": "trunk_runner"
        })
        return {
            "score": result.get("overall_score", 0.0),
            "battery_result": result.get("battery_result"),
            "minted": result.get("minted", False),
            "failure_reason": result.get("failure_reason", "")
        }

    async def run(
        self,
        queue_name: str = "sda_spread",
        concurrency: int = 10,
        max_experiments: int = 700
    ) -> dict:
        """Execute the full Karpathy Loop. Never asks the human."""
        queue = EXPERIMENT_QUEUES.get(queue_name, EXPERIMENT_QUEUES["sda_spread"])
        queue = queue[:max_experiments]

        print(f"[Trunk] Starting {len(queue)} experiments | "
              f"queue={queue_name} | concurrency={concurrency}")

        batch_result = await self.dgm.run_batch(
            experiment_queue=queue,
            child_entity_fn=self._child_entity_fn,
            concurrency=concurrency
        )

        # Morning delta review — always emit regardless of time
        await self._morning_delta_review(batch_result)
        return batch_result

    async def _morning_delta_review(self, result: dict):
        """Emit delta review to Telegram + metarom. Shopify overnight gain pattern."""
        summary = (
            f"🌅 EVEZ-OS Trunk Delta Review\n"
            f"Experiments: {result['total']}\n"
            f"Kept: {result['kept']} ({result['keep_rate']:.1%})\n"
            f"Best Score: {result['best_score']:.4f}\n"
            f"Trunk Version: v{result['trunk_version']}\n"
            f"Session Duration: {(time.time() - self.session_start) / 3600:.1f}h"
        )

        # Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                async with httpx.AsyncClient(timeout=5) as c:
                    await c.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={"chat_id": TELEGRAM_CHAT_ID, "text": summary}
                    )
            except Exception:
                pass

        # metarom
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                await c.post(
                    f"{METAROM_URL}/memory/write",
                    json={
                        "key": f"delta_review:{int(time.time())}",
                        "content": json.dumps({**result, "summary": summary}),
                        "tags": ["delta_review", "trunk"]
                    }
                )
        except Exception:
            pass

        print(summary)


async def main():
    import sys
    queue = sys.argv[1] if len(sys.argv) > 1 else "sda_spread"
    concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    runner = TrunkRunner()
    result = await runner.run(queue_name=queue, concurrency=concurrency)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
