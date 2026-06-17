"""
Trade Executor — Places orders on Polymarket CLOB via py-clob-client.
Supports dry_run mode (log only) and live mode (real trades).
"""
import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from config import config

# ─── Trade Record ────────────────────────────────────────────

@dataclass
class Trade:
    """Record of an executed or simulated trade."""
    timestamp: str
    market_question: str
    market_url: str
    condition_id: str
    side: str           # YES or NO
    price: float
    size_usd: float
    shares: float
    max_payoff: float
    multiplier: float
    score: float
    reasoning: str
    mode: str           # dry_run or live
    order_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None


# ─── Executor ────────────────────────────────────────────────

class TradeExecutor:
    """Executes trades on Polymarket CLOB or simulates in dry_run mode."""

    def __init__(self):
        self.mode = config.mode
        self.trades: list[Trade] = []
        self.total_spent = 0.0
        self.budget = config.strategy.total_budget
        self.client = None

        if self.mode == "live":
            self._init_clob_client()

    def _init_clob_client(self):
        """Initialize py-clob-client for live trading."""
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import ApiCreds

            creds = ApiCreds(
                api_key=config.poly.api_key,
                api_secret=config.poly.api_secret,
                api_passphrase=config.poly.passphrase,
            )

            self.client = ClobClient(
                host=config.poly.clob_url,
                key=config.wallet.private_key,
                chain_id=137,  # Polygon mainnet
                creds=creds,
            )
            print("[EXECUTOR] ✅ CLOB client initialized — LIVE MODE")

        except ImportError:
            print("[EXECUTOR] ⚠️ py-clob-client not installed. Falling back to dry_run.")
            self.mode = "dry_run"
        except Exception as e:
            print(f"[EXECUTOR] ⚠️ CLOB init failed: {e}. Falling back to dry_run.")
            self.mode = "dry_run"

    def can_afford(self, size_usd: float) -> bool:
        """Check if within budget."""
        return (self.total_spent + size_usd) <= self.budget

    def execute(self, scored_market) -> Trade:
        """Execute a trade based on scored market."""
        from scanner import ScoredMarket

        market = scored_market.market
        side = scored_market.recommended_side
        price = market.yes_price if side == "YES" else market.no_price
        size_usd = scored_market.recommended_size

        # Budget check
        if not self.can_afford(size_usd):
            remaining = self.budget - self.total_spent
            if remaining <= 0.01:
                return self._make_trade(
                    market, side, price, 0, 0, 0, scored_market,
                    status="skipped", error="Budget exhausted"
                )
            size_usd = remaining

        shares = size_usd / price if price > 0 else 0
        max_payoff = shares * 1.0  # $1 per share if correct
        multiplier = max_payoff / size_usd if size_usd > 0 else 0

        trade = self._make_trade(
            market, side, price, size_usd, shares, max_payoff, scored_market
        )

        if self.mode == "live":
            trade = self._execute_live(trade, market, side, price, size_usd)
        else:
            trade = self._execute_dry_run(trade)

        if trade.status == "filled" or trade.status == "simulated":
            self.total_spent += size_usd

        self.trades.append(trade)
        return trade

    def _execute_live(self, trade: Trade, market, side, price, size_usd) -> Trade:
        """Place real order on Polymarket CLOB."""
        if not self.client:
            trade.status = "failed"
            trade.error = "No CLOB client"
            return trade

        try:
            from py_clob_client.clob_types import OrderArgs, OrderType

            # Determine token_id based on side
            tokens = market.tokens
            if not tokens or len(tokens) < 2:
                trade.status = "failed"
                trade.error = "No token IDs available"
                return trade

            token_id = tokens[0] if side == "YES" else tokens[1]

            order_args = OrderArgs(
                price=price,
                size=trade.shares,
                side="BUY",
                token_id=token_id,
            )

            # Create and post limit order
            signed_order = self.client.create_order(order_args)
            resp = self.client.post_order(signed_order, OrderType.GTC)

            trade.order_id = resp.get("orderID", resp.get("id", "unknown"))
            trade.status = "filled"
            print(f"[EXECUTOR] 🟢 LIVE ORDER: {side} {market.question[:50]}... @ {price} | ${size_usd:.2f}")

        except Exception as e:
            trade.status = "failed"
            trade.error = str(e)
            print(f"[EXECUTOR] 🔴 ORDER FAILED: {e}")

        return trade

    def _execute_dry_run(self, trade: Trade) -> Trade:
        """Simulate trade execution."""
        trade.status = "simulated"
        trade.order_id = f"DRY-{int(time.time())}"
        print(
            f"[DRY RUN] 📝 {trade.side} {trade.market_question[:50]}... "
            f"@ ${trade.price:.3f} | ${trade.size_usd:.2f} → "
            f"${trade.max_payoff:.2f} ({trade.multiplier:.1f}x)"
        )
        return trade

    def _make_trade(self, market, side, price, size_usd, shares, max_payoff, scored_market, status="pending", error=None) -> Trade:
        return Trade(
            timestamp=datetime.now(timezone.utc).isoformat(),
            market_question=market.question,
            market_url=market.url,
            condition_id=market.condition_id,
            side=side,
            price=price,
            size_usd=size_usd,
            shares=shares,
            max_payoff=max_payoff,
            multiplier=max_payoff / size_usd if size_usd > 0 else 0,
            score=scored_market.score,
            reasoning=scored_market.reasoning,
            mode=self.mode,
            status=status,
            error=error,
        )

    def get_portfolio_summary(self) -> dict:
        """Return portfolio state."""
        active = [t for t in self.trades if t.status in ("filled", "simulated")]
        return {
            "total_trades": len(active),
            "total_spent": sum(t.size_usd for t in active),
            "total_max_payoff": sum(t.max_payoff for t in active),
            "budget_remaining": self.budget - self.total_spent,
            "avg_multiplier": (
                sum(t.multiplier for t in active) / len(active)
                if active else 0
            ),
            "trades": [asdict(t) for t in active],
        }

    def save_trades_log(self, path: str = "trades_log.json"):
        """Persist all trades to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(t) for t in self.trades],
                f, indent=2, ensure_ascii=False,
            )
        print(f"[EXECUTOR] 💾 Trades saved to {path}")
