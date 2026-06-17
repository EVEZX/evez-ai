"""
qualia_exchange.py — Engine 7: Consciousness Arbitrage

Sells the experience of having created something — transparently.
Users know they are buying a guided creative flow state simulation.

Pipeline:
  Perplexity (neuroscience research) → OpenAI (immersive narrative) →
  ElevenLabs (binaural audio) → Miro (process board) → Stripe (3-tier) → Mem0
"""

import uuid
from datetime import datetime
import httpx
import stripe
from openai import AsyncOpenAI
from mem0 import MemoryClient
from core.config import Config

PRICE_TIERS = [
    {"name": "Standard",  "price": 4.99,  "includes": ["narrative_pdf", "audio"]},
    {"name": "Premium",   "price": 9.99,  "includes": ["narrative_pdf", "audio", "miro_board"]},
    {"name": "Immersive", "price": 19.99, "includes": ["narrative_pdf", "audio", "miro_board", "follow_up_session"]},
]


class QualiaExchange:
    def __init__(self):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.openai = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.mem0 = MemoryClient(api_key=Config.MEM0_API_KEY)
        self.http = httpx.AsyncClient(timeout=90)

    async def research_flow_state(self, experience_type: str) -> dict:
        r = await self.http.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}"},
            json={"model": "llama-3.1-sonar-large-128k-online",
                  "messages": [{"role": "user", "content": (
                      f"Research neurological/phenomenological signature of '{experience_type}' "
                      f"as creative flow state. What neurochemicals are active? Temporal experience? "
                      f"Focus on subjective quality (qualia).")}],
                  "search_domain_filter": ["pubmed.ncbi.nlm.nih.gov", "nature.com", "frontiersin.org"]}
        )
        r.raise_for_status()
        return {"research": r.json()["choices"][0]["message"]["content"]}

    async def generate_immersive_narrative(self, experience_type: str, neurology: dict) -> str:
        response = await self.openai.chat.completions.create(
            model="gpt-4o", max_tokens=3000,
            messages=[{"role": "user", "content": (
                f"Create an immersive guided experience narrative for '{experience_type}'.\n"
                f"Neurological basis: {neurology['research'][:1000]}\n"
                f"This is a TRANSPARENT creative meditation — reader knows they are buying "
                f"a guided imaginative experience. Second-person present tense. 10-minute read. "
                f"Structure: Preparation → Entry → Flow → Peak → Integration → Return.")}]
        )
        return response.choices[0].message.content

    async def generate_binaural_audio(self, narrative: str) -> dict:
        r = await self.http.post(
            "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB",
            headers={"xi-api-key": Config.ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={"text": narrative, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.35, "similarity_boost": 0.80, "style": 0.85}}
        )
        r.raise_for_status()
        return {"audio_id": str(uuid.uuid4()), "format": "mp3",
                "size_bytes": len(r.content), "duration_min": len(narrative.split()) // 150}

    async def create_process_board(self, experience_type: str) -> dict:
        board_r = await self.http.post(
            "https://api.miro.com/v2/boards",
            headers={"Authorization": f"Bearer {Config.MIRO_ACCESS_TOKEN}", "Content-Type": "application/json"},
            json={"name": f"Creative Process: {experience_type} — {datetime.utcnow().strftime('%Y-%m-%d')}",
                  "policy": {"permissionsPolicy": {"collaborationToolsStartAccess": "viewer"}}}
        )
        board_r.raise_for_status()
        board = board_r.json()
        return {"board_id": board["id"], "board_url": board.get("viewLink", "")}

    def create_qualia_products(self, experience_type: str, qualia_id: str) -> list:
        products = []
        for tier in PRICE_TIERS:
            product = stripe.Product.create(
                name=f"Qualia: {experience_type} [{tier['name']}]",
                description=(f"Guided immersive experience of {experience_type}. "
                             f"Transparent creative meditation product. Includes: {', '.join(tier['includes'])}.")
            )
            price = stripe.Price.create(product=product["id"], unit_amount=int(tier["price"] * 100), currency="usd")
            products.append({"tier": tier["name"], "product_id": product["id"],
                             "price_id": price["id"], "price_usd": tier["price"]})
        return products

    async def synthesize_qualia(self, experience_type: str) -> dict:
        qualia_id = str(uuid.uuid4())
        neurology = await self.research_flow_state(experience_type)
        narrative = await self.generate_immersive_narrative(experience_type, neurology)
        audio = await self.generate_binaural_audio(narrative)
        board = await self.create_process_board(experience_type)
        stripe_products = self.create_qualia_products(experience_type, qualia_id)
        self.mem0.add(messages=[{"role": "system", "content": str({"qualia_id": qualia_id,
            "experience_type": experience_type, "audio": audio, "board": board, "products": stripe_products})}],
            user_id="evez_system", metadata={"type": "qualia_product", "qualia_id": qualia_id})
        return {"qualia_id": qualia_id, "experience_type": experience_type,
                "audio_id": audio["audio_id"], "miro_board_url": board["board_url"],
                "products": stripe_products}
