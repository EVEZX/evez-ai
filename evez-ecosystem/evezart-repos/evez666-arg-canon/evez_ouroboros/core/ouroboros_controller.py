"""
ouroboros_controller.py — Meta-orchestration

Daily self-reinforcing cycle:
  1. Retrocausal  → predict creative movements
  2. VoidForge   → forge impossible versions of predicted movements
  3. Entropy     → entropic assets from void categories
  4. Qualia      → sell experience of comprehending each engine
  5. Revenue aggregation + reinvestment
  6. GitHub commit of cycle state
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import stripe
import httpx
from mem0 import MemoryClient
from core.config import Config
from engines.entropy_engine import EntropyEngine
from engines.void_forge import VoidForge
from engines.retrocausal_engine import RetrocausalEngine
from engines.qualia_exchange import QualiaExchange

STATE_FILE = Path("state/cycle_state.json")


class OuroborosController:
    def __init__(self):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.entropy     = EntropyEngine()
        self.void        = VoidForge()
        self.retrocausal = RetrocausalEngine()
        self.qualia      = QualiaExchange()
        self.mem0        = MemoryClient(api_key=Config.MEM0_API_KEY)
        self.http        = httpx.AsyncClient(timeout=60)

    async def run_cycle(self) -> dict:
        cycle_start = datetime.utcnow().isoformat()
        print(f"\n{'='*60}\n[Ouroboros] Cycle: {cycle_start}\n{'='*60}")
        state = {"cycle_start": cycle_start, "futures": [], "voids": [],
                 "entropic_assets": [], "qualia_products": [], "revenue": {}, "allocation": {}}

        # Step 1: Retrocausal
        try:
            state["futures"] = await self.retrocausal.mine_future_entropy()
            print(f"  Retrocausal ✓ {len(state['futures'])} futures")
        except Exception as e:
            print(f"  Retrocausal ✗ {e}")

        # Step 2: VoidForge
        for f in state["futures"][:2]:
            try:
                void = await self.void.forge_void(f"{f['movement']} — impossible optimization")
                state["voids"].append(void)
                print(f"  VoidForge ✓ {void['title']}")
            except Exception as e:
                print(f"  VoidForge ✗ {e}")
        for cat in ["perfect trend prediction", "lossless creative entropy"]:
            try:
                void = await self.void.forge_void(category=cat)
                state["voids"].append(void)
            except Exception as e:
                print(f"  MetaVoid ✗ {e}")

        # Step 3: EntropyEngine
        for void in state["voids"][:2]:
            try:
                asset = await self.entropy.create_entropic_asset(f"Visual abstraction: {void['title']}")
                state["entropic_assets"].append(asset)
                print(f"  Entropy ✓ {asset['master_id'][:8]}")
            except Exception as e:
                print(f"  Entropy ✗ {e}")

        # Step 4: QualiaExchange
        for experience in [
            "predicting a creative movement before it exists",
            "forging an artwork that cannot be made",
            "watching something beautiful degrade into noise",
        ]:
            try:
                q = await self.qualia.synthesize_qualia(experience_type=experience)
                state["qualia_products"].append(q)
                print(f"  Qualia ✓ {experience[:50]}")
            except Exception as e:
                print(f"  Qualia ✗ {e}")

        # Step 5: Revenue
        try:
            balance = stripe.Balance.retrieve()
            total = sum(b["amount"] for b in balance["available"]) / 100
            state["revenue"] = {"total_available": total, "currency": "usd"}
            state["allocation"] = {
                "infrastructure": round(total * 0.30, 2),
                "acquisition":    round(total * 0.20, 2),
                "development":    round(total * 0.20, 2),
                "bounties":       round(total * 0.15, 2),
                "reserve":        round(total * 0.15, 2),
            }
            print(f"  Revenue ✓ ${total:,.2f}")
        except Exception as e:
            print(f"  Revenue ✗ {e}")

        # Step 6: Commit state
        state["cycle_end"] = datetime.utcnow().isoformat()
        STATE_FILE.parent.mkdir(exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
        print("[Ouroboros] Cycle complete.")
        return state


async def main():
    await OuroborosController().run_cycle()

if __name__ == "__main__":
    asyncio.run(main())
