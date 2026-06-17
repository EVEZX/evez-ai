"""
entropy_engine.py — Engine 6: Degradation Economics

Creates "Entropic Assets": AI-generated images degraded through 21 format states,
each state sold as a separate NFT. Value increases with entropy.
Self-destruct logic: NFT decays further when view threshold is crossed.

Pipeline:
  AllImages AI → CloudConvert/ConvertAPI → Alchemy NFT × 21 → Stripe auction × 21
  Ably realtime view counter → decay trigger → Mem0 master state
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

import httpx
import stripe
import cloudconvert
from mem0 import MemoryClient
from ably import AblyRealtime

from core.config import Config


# ── Degradation ladder ────────────────────────────────────────────────────────

DEGRADATION_STATES = [
    {"format": "PNG",       "quality": 100, "generation": 0},
    {"format": "PNG",       "quality": 90,  "generation": 1},
    {"format": "JPEG",      "quality": 95,  "generation": 2},
    {"format": "JPEG",      "quality": 85,  "generation": 3},
    {"format": "JPEG",      "quality": 75,  "generation": 4},
    {"format": "JPEG",      "quality": 60,  "generation": 5},
    {"format": "JPEG",      "quality": 45,  "generation": 6},
    {"format": "JPEG",      "quality": 30,  "generation": 7},
    {"format": "JPEG",      "quality": 15,  "generation": 8},
    {"format": "GIF",       "colors": 256,  "generation": 9},
    {"format": "GIF",       "colors": 128,  "generation": 10},
    {"format": "GIF",       "colors": 64,   "generation": 11},
    {"format": "GIF",       "colors": 32,   "generation": 12},
    {"format": "GIF",       "colors": 16,   "generation": 13},
    {"format": "GIF",       "colors": 8,    "generation": 14},
    {"format": "BMP",       "depth": 24,    "generation": 15},
    {"format": "BMP",       "depth": 16,    "generation": 16},
    {"format": "BMP",       "depth": 8,     "generation": 17},
    {"format": "corrupted", "method": "bit_rot",     "generation": 18},
    {"format": "corrupted", "method": "packet_loss", "generation": 19},
    {"format": "corrupted", "method": "entropy_max", "generation": 20},
]

VIEW_THRESHOLD_BASE = 1000
VIEW_THRESHOLD_STEP = 40
BASE_PRICE_MULTIPLIER = 0.5


class EntropyEngine:
    def __init__(self):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.mem0 = MemoryClient(api_key=Config.MEM0_API_KEY)
        self.http = httpx.AsyncClient(timeout=60)
        cloudconvert.configure(api_key=Config.CLOUDCONVERT_API_KEY)

    async def generate_master(self, prompt: str) -> dict:
        response = await self.http.post(
            "https://api.all-images.ai/v1/images/generations",
            headers={"Authorization": f"Bearer {Config.ALL_IMAGES_API_KEY}"},
            json={"prompt": prompt, "model": "flux-pro", "width": 2048, "height": 2048,
                  "output_format": "png", "quality": "maximum"}
        )
        response.raise_for_status()
        data = response.json()
        return {"id": str(uuid.uuid4()), "prompt": prompt, "url": data["data"][0]["url"],
                "format": "PNG", "base_value": 100, "created_at": datetime.utcnow().isoformat()}

    async def degrade_to_state(self, source_url: str, state: dict) -> str:
        fmt = state["format"]
        if fmt == "corrupted":
            return await self._apply_corruption(source_url, state["method"])
        job = cloudconvert.Job.create(payload={"tasks": {
            "import-url": {"operation": "import/url", "url": source_url},
            "convert": {"operation": "convert", "input": "import-url",
                        "output_format": fmt.lower(), "engine_options": self._engine_options(state)},
            "export": {"operation": "export/url", "input": "convert"},
        }})
        while job["status"] not in ("finished", "error"):
            await asyncio.sleep(3)
            job = cloudconvert.Job.find(id=job["id"])
        if job["status"] == "error":
            raise RuntimeError(f"CloudConvert error gen {state['generation']}")
        export_task = next(t for t in job["tasks"] if t["name"] == "export")
        return export_task["result"]["files"][0]["url"]

    def _engine_options(self, state: dict) -> dict:
        fmt = state["format"]
        if fmt in ("JPEG", "PNG"): return {"quality": state.get("quality", 80)}
        if fmt == "GIF": return {"colors": state.get("colors", 256)}
        if fmt == "BMP": return {"bit_depth": state.get("depth", 24)}
        return {}

    async def _apply_corruption(self, url: str, method: str) -> str:
        import random, os
        r = await self.http.get(url)
        data = bytearray(r.content)
        if method == "bit_rot":
            for _ in range(len(data) // 20):
                i = random.randint(100, len(data) - 1)
                data[i] ^= random.randint(1, 255)
        elif method == "packet_loss":
            for _ in range(len(data) // 512 // 4):
                start = random.randint(100, len(data) - 513)
                data[start:start + 512] = b'\x00' * 512
        elif method == "entropy_max":
            keep = 200
            data[keep:] = os.urandom(len(data) - keep)
        return await self._upload_bytes(bytes(data), "corrupted.png")

    async def _upload_bytes(self, data: bytes, filename: str) -> str:
        import base64
        b64 = base64.b64encode(data).decode()
        r = await self.http.post(
            "https://v2.convertapi.com/upload",
            headers={"Authorization": f"Bearer {Config.CONVERTAPI_SECRET}"},
            json={"file": b64, "filename": filename}
        )
        r.raise_for_status()
        return r.json()["Url"]

    async def mint_nft(self, master_id: str, generation: int, file_url: str, view_threshold: int) -> dict:
        metadata = {
            "name": f"Entropic Asset #{master_id[:8]} — Gen {generation}",
            "description": f"Generation {generation}/20. Self-destructs after {view_threshold} views.",
            "image": file_url,
            "attributes": [
                {"trait_type": "generation", "value": generation},
                {"trait_type": "entropy_level", "value": round(generation / 20, 2)},
                {"trait_type": "view_threshold", "value": view_threshold},
                {"trait_type": "status", "value": "intact"},
            ]
        }
        r = await self.http.post(
            f"https://upload.alchemyapi.io/v2/{Config.ALCHEMY_API_KEY}/uploadNFTMetadata", json=metadata)
        r.raise_for_status()
        token_uri = r.json()["metadataUrl"]
        mint_r = await self.http.post(
            f"https://polygon-mainnet.g.alchemy.com/nft/v2/{Config.ALCHEMY_API_KEY}/mintNFT",
            json={"contractAddress": Config.ALCHEMY_ENTROPIC_CONTRACT, "tokenURI": token_uri})
        mint_r.raise_for_status()
        return {"token_id": mint_r.json().get("tokenId"), "token_uri": token_uri,
                "contract": Config.ALCHEMY_ENTROPIC_CONTRACT}

    def create_stripe_product(self, master_id, prompt, generation, base_value, nft_address, view_threshold) -> dict:
        price_usd = round(base_value * (1 + generation * BASE_PRICE_MULTIPLIER), 2)
        product = stripe.Product.create(
            name=f"{prompt[:40]}… [Gen {generation}/20]",
            description=f"Entropy state {generation}/20. View threshold: {view_threshold}. NFT: {nft_address}",
            metadata={"master_id": master_id, "generation": str(generation)}
        )
        price = stripe.Price.create(product=product["id"], unit_amount=int(price_usd * 100), currency="usd")
        return {"product_id": product["id"], "price_id": price["id"], "price_usd": price_usd}

    async def create_entropic_asset(self, prompt: str) -> dict:
        master = await self.generate_master(prompt)
        master_id = master["id"]
        states = []
        current_url = master["url"]
        for state_def in DEGRADATION_STATES:
            gen = state_def["generation"]
            view_threshold = VIEW_THRESHOLD_BASE - (gen * VIEW_THRESHOLD_STEP)
            degraded_url = await self.degrade_to_state(current_url, state_def)
            nft = await self.mint_nft(master_id, gen, degraded_url, view_threshold)
            stripe_data = self.create_stripe_product(master_id, prompt, gen, master["base_value"],
                                                      nft["token_id"], view_threshold)
            states.append({"generation": gen, "file_url": degraded_url, "nft": nft, "stripe": stripe_data})
            current_url = degraded_url
        self.mem0.add(messages=[{"role": "system", "content": str({"master": master, "states": states})}],
                      user_id="evez_system", metadata={"type": "entropic_master", "master_id": master_id})
        return {"master_id": master_id, "prompt": prompt, "total_states": len(states)}
