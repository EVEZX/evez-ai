"""
Market Scanner — Fetches all Polymarket markets, filters by speed,
pulls live evidence feeds, scores every contract.
"""
import time
import requests
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional
from config import config

# ─── Data Models ─────────────────────────────────────────────

@dataclass
class Market:
    """A single YES/NO market on Polymarket."""
    condition_id: str
    question: str
    slug: str
    end_date: datetime
    volume: float
    liquidity: float
    yes_price: float
    no_price: float
    category: str
    tokens: list
    event_slug: str = ""

    @property
    def days_to_resolve(self) -> float:
        delta = self.end_date - datetime.now(timezone.utc)
        return max(delta.total_seconds() / 86400, 0)

    @property
    def best_payoff(self) -> float:
        """Best multiplier: buy cheapest side."""
        cheap = min(self.yes_price, self.no_price)
        if cheap <= 0:
            return 0
        return 1.0 / cheap

    @property
    def best_side(self) -> str:
        return "YES" if self.yes_price <= self.no_price else "NO"

    @property
    def best_price(self) -> float:
        return min(self.yes_price, self.no_price)

    @property
    def url(self) -> str:
        return f"https://polymarket.com/event/{self.event_slug}"


@dataclass
class Evidence:
    """Live evidence data point."""
    source: str
    signal: str
    value: float
    timestamp: datetime
    relevance_tags: list


@dataclass
class ScoredMarket:
    """Market with computed score."""
    market: Market
    score: float
    speed_score: float
    payoff_score: float
    evidence_score: float
    volume_score: float
    recommended_side: str
    recommended_size: float
    reasoning: str


# ─── Polymarket API Client ───────────────────────────────────

class PolymarketScanner:
    """Scans Polymarket's Gamma API for all active markets."""

    def __init__(self):
        self.gamma_url = config.poly.gamma_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SpeedRunBot/1.0"
        })

    def fetch_all_markets(self, limit: int = 500) -> list[Market]:
        """Fetch active markets from Gamma API."""
        markets = []
        offset = 0
        batch_size = 100

        while offset < limit:
            try:
                resp = self.session.get(
                    f"{self.gamma_url}/markets",
                    params={
                        "limit": batch_size,
                        "offset": offset,
                        "active": True,
                        "closed": False,
                        "order": "volume",
                        "ascending": False,
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()

                if not data:
                    break

                for m in data:
                    try:
                        end_str = m.get("endDate") or m.get("end_date_iso", "")
                        if not end_str:
                            continue

                        end_date = datetime.fromisoformat(
                            end_str.replace("Z", "+00:00")
                        )

                        outcomes_prices = m.get("outcomePrices", "")
                        if isinstance(outcomes_prices, str):
                            # Parse "[\"0.73\",\"0.27\"]" format
                            import json
                            try:
                                prices = json.loads(outcomes_prices)
                                yes_price = float(prices[0]) if len(prices) > 0 else 0.5
                                no_price = float(prices[1]) if len(prices) > 1 else 0.5
                            except:
                                yes_price = 0.5
                                no_price = 0.5
                        elif isinstance(outcomes_prices, list):
                            yes_price = float(outcomes_prices[0]) if outcomes_prices else 0.5
                            no_price = float(outcomes_prices[1]) if len(outcomes_prices) > 1 else 0.5
                        else:
                            yes_price = float(m.get("bestBid", 0.5))
                            no_price = 1.0 - yes_price

                        market = Market(
                            condition_id=m.get("conditionId", m.get("id", "")),
                            question=m.get("question", ""),
                            slug=m.get("slug", ""),
                            end_date=end_date,
                            volume=float(m.get("volume", 0) or 0),
                            liquidity=float(m.get("liquidity", 0) or 0),
                            yes_price=yes_price,
                            no_price=no_price,
                            category=m.get("category", ""),
                            tokens=m.get("clobTokenIds", []),
                            event_slug=m.get("eventSlug", m.get("slug", "")),
                        )
                        markets.append(market)
                    except Exception as e:
                        continue

                offset += batch_size

            except Exception as e:
                print(f"[SCANNER] API error at offset {offset}: {e}")
                break

        return markets

    def filter_speed_markets(self, markets: list[Market]) -> list[Market]:
        """Filter to fast-resolving markets only."""
        max_days = config.strategy.max_days
        min_payoff = config.strategy.min_payoff

        filtered = []
        for m in markets:
            if m.days_to_resolve > max_days:
                continue
            if m.best_payoff < min_payoff:
                continue
            if m.volume < 1000:  # Skip dead markets
                continue
            filtered.append(m)

        return sorted(filtered, key=lambda m: m.days_to_resolve)


# ─── Evidence Engine ─────────────────────────────────────────

class EvidenceEngine:
    """Pulls live data from multiple sources for evidence-based scoring."""

    def __init__(self):
        self.session = requests.Session()
        self.cache = {}
        self.cache_ttl = 60  # seconds

    def get_crypto_prices(self) -> dict:
        """Fetch live crypto prices from CoinGecko."""
        cache_key = "crypto_prices"
        if cache_key in self.cache:
            ts, data = self.cache[cache_key]
            if time.time() - ts < self.cache_ttl:
                return data

        try:
            resp = self.session.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum,solana,cardano,ripple,polkadot,chainlink,avalanche-2,uniswap,litecoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_7d_change": "true",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            self.cache[cache_key] = (time.time(), data)
            return data
        except Exception as e:
            print(f"[EVIDENCE] CoinGecko error: {e}")
            return {}

    def get_crypto_momentum(self) -> list[Evidence]:
        """Compute momentum signals from crypto prices."""
        prices = self.get_crypto_prices()
        evidence = []

        for coin, data in prices.items():
            change_24h = data.get("usd_24h_change", 0) or 0
            evidence.append(Evidence(
                source="coingecko",
                signal=f"{coin}_24h_momentum",
                value=change_24h,
                timestamp=datetime.now(timezone.utc),
                relevance_tags=["crypto", coin, "momentum"],
            ))

        return evidence

    def get_fear_greed_index(self) -> Optional[Evidence]:
        """Fetch crypto Fear & Greed Index."""
        try:
            resp = self.session.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            value = int(data["data"][0]["value"])
            return Evidence(
                source="alternative.me",
                signal="fear_greed_index",
                value=value,
                timestamp=datetime.now(timezone.utc),
                relevance_tags=["crypto", "sentiment", "fear_greed"],
            )
        except:
            return None

    def collect_all_evidence(self) -> list[Evidence]:
        """Aggregate all evidence sources."""
        evidence = []
        evidence.extend(self.get_crypto_momentum())

        fng = self.get_fear_greed_index()
        if fng:
            evidence.append(fng)

        return evidence


# ─── Scoring Engine ──────────────────────────────────────────

class ScoringEngine:
    """Scores markets on speed × payoff × evidence × volume."""

    # Keywords that map evidence to market categories
    CRYPTO_KEYWORDS = ["bitcoin", "btc", "ethereum", "eth", "crypto", "solana", "sol"]
    GEO_KEYWORDS = ["iran", "strike", "war", "military", "sanctions"]
    AI_KEYWORDS = ["ai", "model", "gpt", "anthropic", "claude", "openai", "gemini"]
    POLITICS_KEYWORDS = ["trump", "biden", "election", "president", "congress", "senate"]

    def score_market(self, market: Market, evidence: list[Evidence]) -> ScoredMarket:
        """Compute composite score for a market."""

        # ── Speed Score (0-25) ──
        # Faster resolution = higher score. Max at <1 day.
        days = market.days_to_resolve
        if days < 0.01:  # minutes
            speed_score = 25.0
        elif days < 1:
            speed_score = 22.0 + (1 - days) * 3
        elif days < 3:
            speed_score = 18.0 + (3 - days) / 2 * 4
        elif days < 7:
            speed_score = 12.0 + (7 - days) / 4 * 6
        elif days < 14:
            speed_score = 5.0 + (14 - days) / 7 * 7
        else:
            speed_score = max(0, 5 - (days - 14) / 7)

        # ── Payoff Score (0-25) ──
        # Higher multiplier = higher score. Max at 10x+.
        payoff = market.best_payoff
        if payoff >= 10:
            payoff_score = 25.0
        elif payoff >= 5:
            payoff_score = 18.0 + (payoff - 5) / 5 * 7
        elif payoff >= 3:
            payoff_score = 12.0 + (payoff - 3) / 2 * 6
        elif payoff >= 2:
            payoff_score = 6.0 + (payoff - 2) * 6
        else:
            payoff_score = max(0, payoff * 3)

        # ── Evidence Score (0-25) ──
        # How much live evidence supports the cheap side
        evidence_score = self._compute_evidence_score(market, evidence)

        # ── Volume/Liquidity Score (0-25) ──
        # Higher volume = more trustworthy price, better execution
        vol = market.volume
        if vol >= 10_000_000:
            volume_score = 25.0
        elif vol >= 1_000_000:
            volume_score = 18.0 + (vol - 1_000_000) / 9_000_000 * 7
        elif vol >= 100_000:
            volume_score = 10.0 + (vol - 100_000) / 900_000 * 8
        elif vol >= 10_000:
            volume_score = 4.0 + (vol - 10_000) / 90_000 * 6
        else:
            volume_score = vol / 10_000 * 4

        # ── Composite Score ──
        total = speed_score + payoff_score + evidence_score + volume_score

        # ── Determine side + reasoning ──
        side = market.best_side
        reasoning = self._generate_reasoning(
            market, speed_score, payoff_score, evidence_score, volume_score
        )

        # ── Position sizing ──
        size = self._compute_size(total, market)

        return ScoredMarket(
            market=market,
            score=total,
            speed_score=speed_score,
            payoff_score=payoff_score,
            evidence_score=evidence_score,
            volume_score=volume_score,
            recommended_side=side,
            recommended_size=size,
            reasoning=reasoning,
        )

    def _compute_evidence_score(self, market: Market, evidence: list[Evidence]) -> float:
        """Score how well live evidence supports the trade."""
        q = market.question.lower()
        score = 0.0

        is_crypto = any(kw in q for kw in self.CRYPTO_KEYWORDS)
        is_geo = any(kw in q for kw in self.GEO_KEYWORDS)
        is_ai = any(kw in q for kw in self.AI_KEYWORDS)

        for ev in evidence:
            if is_crypto and "crypto" in ev.relevance_tags:
                # Negative momentum supports "price drops below X" bets
                if "momentum" in ev.signal:
                    if ev.value < -3:
                        score += 5  # Strong bearish momentum
                    elif ev.value < 0:
                        score += 2
                    elif ev.value > 3:
                        score -= 2  # Bullish contradicts crash bet

                # Fear index supports crash bets
                if ev.signal == "fear_greed_index":
                    if ev.value < 25:  # Extreme fear
                        score += 5
                    elif ev.value < 40:
                        score += 3
                    elif ev.value > 60:
                        score -= 2

            if is_geo and "geopolitical" in ev.relevance_tags:
                score += abs(ev.value) * 2

        return max(0, min(25, score))

    def _generate_reasoning(self, market, spd, pay, evi, vol) -> str:
        """Generate human-readable reasoning."""
        parts = []
        if spd > 18:
            parts.append(f"Ultra-fast: resolves in {market.days_to_resolve:.1f}d")
        elif spd > 10:
            parts.append(f"Fast: resolves in {market.days_to_resolve:.0f}d")

        if pay > 18:
            parts.append(f"High payoff: {market.best_payoff:.1f}x")
        elif pay > 10:
            parts.append(f"Decent payoff: {market.best_payoff:.1f}x")

        if evi > 15:
            parts.append("Strong evidence alignment")
        elif evi > 8:
            parts.append("Moderate evidence support")

        if vol > 18:
            parts.append(f"Deep liquidity: ${market.volume:,.0f}")
        elif vol < 8:
            parts.append("⚠️ Thin liquidity — slippage risk")

        return " | ".join(parts) if parts else "Marginal"

    def _compute_size(self, score: float, market: Market) -> float:
        """Kelly-inspired position sizing."""
        max_bet = config.strategy.max_bet_size
        budget = config.strategy.total_budget

        if score >= 80:
            pct = 0.30
        elif score >= 65:
            pct = 0.20
        elif score >= 50:
            pct = 0.15
        else:
            pct = 0.10

        size = budget * pct
        return min(size, max_bet)
