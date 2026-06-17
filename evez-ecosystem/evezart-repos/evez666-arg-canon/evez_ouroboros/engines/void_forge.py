"""
void_forge.py — Engine 4: Negative Space Capitalization

Creates "Void Art": AI-generated specs for artworks that cannot exist.
Each void is an NFT + Stripe product + active bounty.
Solver gets bounty; void owner gets 5% royalty on all future instances.

Pipeline:
  Perplexity (impossibility research) → OpenAI (void spec) →
  Alchemy NFT → Stripe product → Agent Mail bounty campaign → Mem0
"""

import uuid
from datetime import datetime
import httpx
import stripe
from openai import AsyncOpenAI
from mem0 import MemoryClient
from core.config import Config


class VoidForge:
    def __init__(self):
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.openai = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.mem0 = MemoryClient(api_key=Config.MEM0_API_KEY)
        self.http = httpx.AsyncClient(timeout=90)

    async def research_impossibilities(self, category: str) -> dict:
        r = await self.http.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {Config.PERPLEXITY_API_KEY}"},
            json={"model": "llama-3.1-sonar-large-128k-online",
                  "messages": [{"role": "user", "content": (
                      f"Research absolute technical, physical, and logical impossibilities "
                      f"in {category} art and creative work. Cite limiting principles.")}],
                  "search_domain_filter": ["arxiv.org", "nature.com", "science.org"]}
        )
        r.raise_for_status()
        return {"raw": r.json()["choices"][0]["message"]["content"], "category": category}

    async def generate_void_spec(self, category: str, impossibilities: dict) -> dict:
        response = await self.openai.chat.completions.create(
            model="gpt-4o", max_tokens=4000,
            messages=[{"role": "user", "content": (
                f"Create a detailed specification for an impossible artwork.\n"
                f"Category: {category}\nKnown impossibilities: {impossibilities['raw']}\n"
                f"Document: title, technical requirements violating physics, material constraints, "
                f"theoretical disproof, emotional impact if possible, fabrication guide (each step fails), "
                f"estimated market value (USD), one-sentence Impossibility Statement.")}]
        )
        text = response.choices[0].message.content
        import re
        value_match = re.search(r"\$[\d,]+", text)
        estimated_value = float(value_match.group().replace("$","").replace(",","")) if value_match else 50000.0
        title_match = re.search(r"(?:Title|1\.)[:\s]+(.+)", text)
        title = title_match.group(1).strip()[:80] if title_match else f"Void: {category}"
        return {"id": str(uuid.uuid4()), "title": title, "category": category,
                "specification": text, "estimated_value": estimated_value,
                "bounty_amount": estimated_value * 0.5, "created_at": datetime.utcnow().isoformat()}

    async def mint_void_nft(self, void_spec: dict) -> dict:
        metadata = {
            "name": void_spec["title"],
            "description": (f"Void Art — ownership of the concept of an impossible "
                            f"{void_spec['category']} work. Bounty: ${void_spec['bounty_amount']:,.0f}"),
            "image": f"{Config.EVEZ_BASE_URL}/void/placeholder.png",
            "attributes": [
                {"trait_type": "bounty_active", "value": True},
                {"trait_type": "bounty_amount", "value": void_spec["bounty_amount"]},
                {"trait_type": "status", "value": "unsolved"},
                {"trait_type": "royalty_rate", "value": 0.05},
            ]
        }
        r = await self.http.post(
            f"https://upload.alchemyapi.io/v2/{Config.ALCHEMY_API_KEY}/uploadNFTMetadata", json=metadata)
        r.raise_for_status()
        token_uri = r.json()["metadataUrl"]
        mint_r = await self.http.post(
            f"https://polygon-mainnet.g.alchemy.com/nft/v2/{Config.ALCHEMY_API_KEY}/mintNFT",
            json={"contractAddress": Config.ALCHEMY_VOID_CONTRACT, "tokenURI": token_uri})
        mint_r.raise_for_status()
        return {"token_id": mint_r.json().get("tokenId"), "token_uri": token_uri,
                "contract": Config.ALCHEMY_VOID_CONTRACT}

    def create_void_product(self, void_spec: dict, nft: dict) -> dict:
        price_usd = max(9.99, round(void_spec["estimated_value"] * 0.01, 2))
        product = stripe.Product.create(
            name=f"Void: {void_spec['title']}",
            description=(f"Ownership of an impossible {void_spec['category']} concept. "
                         f"Active bounty: ${void_spec['bounty_amount']:,.0f}. 5% royalty if solved."),
            metadata={"void_id": void_spec["id"], "bounty_amount": str(void_spec["bounty_amount"])}
        )
        price = stripe.Price.create(product=product["id"], unit_amount=int(price_usd * 100), currency="usd")
        return {"product_id": product["id"], "price_id": price["id"], "price_usd": price_usd}

    async def forge_void(self, category: str) -> dict:
        impossibilities = await self.research_impossibilities(category)
        void_spec = await self.generate_void_spec(category, impossibilities)
        nft = await self.mint_void_nft(void_spec)
        stripe_data = self.create_void_product(void_spec, nft)
        self.mem0.add(messages=[{"role": "system", "content": str({"void_spec": void_spec, "nft": nft, "stripe": stripe_data})}],
                      user_id="evez_system", metadata={"type": "void_asset", "void_id": void_spec["id"]})
        return {"void_id": void_spec["id"], "title": void_spec["title"],
                "nft_token_id": nft["token_id"], "product_id": stripe_data["product_id"],
                "bounty": void_spec["bounty_amount"]}
