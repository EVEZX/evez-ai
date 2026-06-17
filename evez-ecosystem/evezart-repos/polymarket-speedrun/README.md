# ⚡ Polymarket Speed-Run Bot v1.0

**Fastest flip. Evidence-driven. Zero bias.**
**Built by SureThing × EVEZ**

A local-first automated trading bot that scans Polymarket for the fastest, highest-payoff,
most falsifiable bets — then executes them automatically through your wallet.

---

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│   Scanner   │───▶│   Evidence   │───▶│    Scoring     │───▶│   Executor   │
│             │    │   Engine     │    │    Engine      │    │              │
│ • Gamma API │    │ • CoinGecko  │    │ • Speed  (25)  │    │ • Dry-run    │
│ • All mrkts │    │ • Fear/Greed │    │ • Payoff (25)  │    │ • Live CLOB  │
│ • Filter    │    │ • Momentum   │    │ • Evidence(25) │    │ • Portfolio  │
│   by speed  │    │ • Headlines  │    │ • Volume (25)  │    │ • Logging    │
└─────────────┘    └──────────────┘    └────────────────┘    └──────────────┘
                                              │
                                       Score 0-100
                                              │
                                     ┌────────▼────────┐
                                     │  Display (Rich)  │
                                     │  Terminal Table   │
                                     └──────────────────┘
```

## Scoring Formula

Each market gets scored 0-100 across four dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| ⚡ Speed | 25 pts | Days until resolution. <1d = max score. |
| 💰 Payoff | 25 pts | Multiplier on cheapest side. 10x+ = max. |
| 🔬 Evidence | 25 pts | Live data alignment (momentum, sentiment). |
| 📊 Volume | 25 pts | Liquidity & market depth. $10M+ = max. |

**Threshold:** Only markets scoring ≥65 (configurable) trigger auto-execution.

**Position sizing:** Kelly-inspired — higher score = larger allocation (10-30% of budget).

---

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd polymarket-speedrun
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your wallet + API keys
```

**Required for live trading:**
- `PRIVATE_KEY` — Your Ethereum wallet private key (used to sign Polygon transactions)
- `POLY_API_KEY` / `POLY_API_SECRET` / `POLY_API_PASSPHRASE` — From Polymarket CLOB API

**Get Polymarket API credentials:**
1. Go to [polymarket.com](https://polymarket.com)
2. Connect your wallet
3. Go to Settings → API → Create API Key
4. Copy key, secret, and passphrase into .env

### 3. Dry Run (Test Mode)

```bash
python main.py --dry-run --once
```

This scans all markets, scores them, and simulates trades without spending anything.

### 4. Live Mode

```bash
# Fund your Polymarket wallet with USDC on Polygon first!
python main.py --live
```

**⚠️ LIVE MODE uses real money. Start with --dry-run to verify behavior.**

### 5. Advanced Options

```bash
# Scan only — no execution, just show rankings
python main.py --scan-only

# Custom budget + bet size
python main.py --budget 50 --max-bet 10

# Faster scan cycle
python main.py --interval 30

# Look further out (30 days instead of 14)
python main.py --max-days 30

# Combined — aggressive scan, live, high budget
python main.py --live --budget 100 --max-bet 20 --interval 30 --max-days 7
```

---

## File Structure

```
polymarket-speedrun/
├── main.py           # Entry point — main loop
├── config.py         # Configuration loader
├── scanner.py        # Market scanner + evidence engine + scoring
├── executor.py       # Trade execution (dry-run + live)
├── display.py        # Rich terminal dashboard
├── .env.example      # Environment template
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## How It Works — Full Cycle

1. **SCAN** — Fetches 500+ active markets from Polymarket Gamma API
2. **FILTER** — Keeps only markets resolving within `MAX_DAYS_TO_RESOLVE` with payoff > `MIN_PAYOFF_MULTIPLIER`
3. **EVIDENCE** — Pulls live crypto prices, 24h momentum, Fear & Greed Index
4. **SCORE** — Computes 0-100 composite score for every filtered market
5. **RANK** — Sorts by score, displays rich table in terminal
6. **EXECUTE** — Auto-buys cheapest side of markets scoring above threshold
7. **LOG** — Saves all trades to timestamped JSON files
8. **REPEAT** — Sleeps `SCAN_INTERVAL` seconds, then loops

The bot stops when:
- Budget is fully deployed
- You press Ctrl+C
- `--once` flag was set

---

## Extending the Evidence Engine

To add new evidence sources, edit `scanner.py` → `EvidenceEngine`:

```python
def get_custom_signal(self) -> list[Evidence]:
    # Fetch from any API
    resp = self.session.get("https://api.example.com/signal")
    data = resp.json()
    return [Evidence(
        source="example",
        signal="custom_metric",
        value=data["metric"],
        timestamp=datetime.now(timezone.utc),
        relevance_tags=["custom", "category"],
    )]
```

Then add it to `collect_all_evidence()` and update `ScoringEngine._compute_evidence_score()`.

**Ideas for evidence sources:**
- News API headlines (sentiment analysis)
- Twitter/X trending topics
- On-chain whale movements
- Options market IV (implied volatility)
- Congressional trade disclosures
- GDELT event data (geopolitical)

---

## Safety

- **Default mode is dry_run** — no real money unless you explicitly set `MODE=live` or `--live`
- **Budget cap** — bot never exceeds `TOTAL_BUDGET`
- **Per-trade cap** — single trade never exceeds `MAX_BET_SIZE`
- **5-second countdown** in live mode before first trade
- **Graceful shutdown** — Ctrl+C saves all trades and exits cleanly
- **Your keys never leave your machine** — everything runs locally

---

## Roadmap

- [ ] WebSocket streaming (real-time price updates instead of polling)
- [ ] Multi-strategy modes (momentum, contrarian, mean-reversion)
- [ ] Telegram/Discord notifications on trade execution
- [ ] Position monitoring & auto-exit on profit targets
- [ ] Backtesting engine against historical Polymarket data
- [ ] Multi-market correlation analysis (correlated bets detector)

---

## License

Built by SureThing × EVEZ. Use at your own risk.
This is experimental software. Prediction markets involve real money and real risk.
Never trade more than you can afford to lose.
