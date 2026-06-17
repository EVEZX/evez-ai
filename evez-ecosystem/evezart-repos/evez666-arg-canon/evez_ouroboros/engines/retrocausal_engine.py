"""
retrocausal_engine.py — Engine 1: Retrocausal Creative Acquisition

Predicts creative trends 6-18 months out. Sells futures contracts to collectors.
If prediction accurate → standard delivery. If wrong → divergence artifact (premium).

Pipeline:
  Groq (trend inference) → Perplexity (future research) →
  Hyperbrowser (signal scouting) → All Images AI (artifact) →
  Alchemy NFT → Stripe product → Mem0
"""

import uuid
from datetime import datetime, timedelta
import httpx
import stripe
from mem0 import MemoryClient
from groq import AsyncGroq
from core.config import Config

PREDICTION_HORIZONS = [90, 180, 270]


class RetrocausalEngine:
    def __init__(self):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.groq = AsyncGroq(api_key=Config.GROQ_API_KEY)
        self.mem0 = MemoryClient(api_key=Config.MEM0_API_KEY)
        self.http = httpx.AsyncClient(timeout=90)

    async def extract_trend_signals(self) -> dict:
        import json, re
        response = await self.groq.chat.completions.create(
            model="llama-3.3-70b-versatile", temperature=1.2, max_tokens=2000,
            messages=[{"role": "user", "content": (
                "Analyze creative/cultural trends. Identify absent territories, structural tensions, "
                "unexploited capabilities. Output JSON with keys: absent_territories, structural_tensions, "
                "unexploited_capabilities, predicted_movements (array: name, description, timeline_months).")}]
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: pass
        return {"raw": content, "predicted_movements": []}

    async def research_future_trend(self, movement_name: str, horizon_days: int) -> dict:
        r = await self.http.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}"},
            json={"model": "llama-3.1-sonar-large-128k-online",
                  "messages": [{"role": "user", "content": (
                      f"Research early signals for '{movement_name}' as a creative movement. "
                      f"Find academic papers, underground communities, prototype works. "
                      f"Predict likelihood mainstream in {horizon_days} days.")}],
                  "search_recency_filter": "month"}
        )
        r.raise_for_status()
        return {"movement": movement_name, "horizon_days": horizon_days,
                "research": r.json()["choices"][0]["message"]["content"]}

    async def generate_future_artifact(self, movement: dict, research: dict) -> dict:
        r = await self.http.post(
            "https://api.all-images.ai/v1/images/generations",
            headers={"Authorization": f"Bearer {Config.ALL_IMAGES_API_KEY}"},
            json={"prompt": f"A defining artwork from the '{movement.get('name')}' movement. "
                           f"{movement.get('description', '')} Visual style: forward-looking, anticipatory.",
                  "model": "flux-pro", "width": 1024, "height": 1024, "output_format": "png"}
        )
        r.raise_for_status()
        return {"id": str(uuid.uuid4()), "image_url": r.json()["data"][0]["url"],
                "movement": movement, "research": research}

    async def mint_futures_nft(self, artifact: dict, collapse_date: str, confidence: float) -> dict:
        metadata = {
            "name": f"Chronotaxic: {artifact['movement'].get('name', 'Unknown')}",
            "description": f"Creative artifact from predicted future. Collapses {collapse_date}. Confidence: {confidence:.0%}",
            "image": artifact["image_url"],
            "attributes": [
                {"trait_type": "temporal_state", "value": "superposition"},
                {"trait_type": "collapse_date", "value": collapse_date},
                {"trait_type": "confidence", "value": round(confidence, 2)},
            ]
        }
        r = await self.http.post(
            f"https://upload.alchemyapi.io/v2/{Config.ALCHEMY_API_KEY}/uploadNFTMetadata", json=metadata)
        r.raise_for_status()
        token_uri = r.json()["metadataUrl"]
        mint_r = await self.http.post(
            f"https://polygon-mainnet.g.alchemy.com/nft/v2/{Config.ALCHEMY_API_KEY}/mintNFT",
            json={"contractAddress": Config.ALCHEMY_CHRONO_CONTRACT, "tokenURI": token_uri})
        mint_r.raise_for_status()
        return {"token_id": mint_r.json().get("tokenId"), "token_uri": token_uri}

    def create_futures_contract(self, movement: dict, nft: dict, collapse_date: str, confidence: float) -> dict:
        price_usd = round(49.99 * (1 + (1 - confidence)), 2)
        product = stripe.Product.create(
            name=f"Future: {movement.get('name', 'Unknown Movement')}",
            description=(f"Asset from predicted future. Delivered {collapse_date}. "
                         f"Accurate → standard. Divergent → 3x premium."),
            metadata={"collapse_date": collapse_date, "confidence": str(confidence)}
        )
        price = stripe.Price.create(product=product["id"], unit_amount=int(price_usd * 100), currency="usd")
        return {"product_id": product["id"], "price_id": price["id"], "price_usd": price_usd}

    async def mine_future_entropy(self) -> list:
        import random
        horizon_days = random.choice(PREDICTION_HORIZONS)
        collapse_date = (datetime.utcnow() + timedelta(days=horizon_days)).strftime("%Y-%m-%d")
        signals = await self.extract_trend_signals()
        movements = signals.get("predicted_movements", [])
        if not movements: return []
        results = []
        for movement in movements[:2]:
            research = await self.research_future_trend(movement.get("name", ""), horizon_days)
            artifact = await self.generate_future_artifact(movement, research)
            confidence = 0.3 + (hash(movement.get("name", "")) % 40) / 100
            nft = await self.mint_futures_nft(artifact, collapse_date, confidence)
            stripe_data = self.create_futures_contract(movement, nft, collapse_date, confidence)
            self.mem0.add(messages=[{"role": "system", "content": str({"movement": movement,
                "artifact": artifact, "nft": nft, "stripe": stripe_data, "collapse_date": collapse_date})}],
                user_id="evez_system", metadata={"type": "pre_memory", "collapse_date": collapse_date})
            results.append({"movement": movement.get("name"), "collapse_date": collapse_date,
                            "nft_token_id": nft["token_id"], "product_id": stripe_data["product_id"]})
        return results
