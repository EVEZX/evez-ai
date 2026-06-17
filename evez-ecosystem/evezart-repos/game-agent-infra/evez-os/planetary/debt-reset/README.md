# Debt Reset — Workstream B
**Module:** planetary/debt-reset | **Cadence:** Weekly (every ~35 rounds) | **Truth Plane:** CANONICAL

## Debt Map Schema
```json
{
  "jurisdiction": "string",
  "sector": "sovereign|municipal|corporate|household",
  "total_debt_usd": 0,
  "gdp_ratio": 0.0,
  "maturity_wall_date": "ISO8601",
  "avg_rate": 0.0,
  "fx_mismatch": true,
  "primary_holders": [],
  "fragility_score": 0.0,
  "falsifier": "what would make this wrong"
}
```

## Fragility Cluster Signals
- Maturity wall within 18 months
- FX mismatch >30% of total debt
- Rate sensitivity: 100bps = >5% primary balance impact
- Debt/GDP >120% + primary deficit
- Rollover risk: >25% maturing in 12 months

## Policy Menu (Modular Packages)
| Package | Mechanism | Jurisdiction |
|---------|-----------|-------------|
| Sovereign restructuring | CAC + standstill + maturity extension | Sovereign |
| Debt-for-climate swap | FV discount → climate adaptation fund | Sovereign |
| Debt-for-health swap | FV discount → health system investment | Sovereign |
| CB liquidity facility | Lender of last resort, collateral rules | All |
| Household relief | Bankruptcy modernization + rate caps | Household |
| Corporate workout | Pre-pack + CoCo + productivity covenant | Corporate |

## Simulator Spec (Vercel)
Inputs:
- Rate shock (+0 to +500bps)
- Growth shock (-5% to +5%)
- FX shock (-30% to +30%)
- Maturity extension (0 to 10 years)

Outputs:
- Default cascade probability
- Refi wall pressure
- Primary balance stress index
- Debt/GDP trajectory (5-year)

## Data Sources
- IMF WEO + DSA databases
- World Bank IDS (International Debt Statistics)
- BIS consolidated banking statistics
- OECD sovereign debt statistics
- Bloomberg/Refinitiv (via Apiverve or API Labz)

## Status
- Schema: DEFINED
- Data: PENDING first import
- Simulator: PENDING Vercel deploy
- Negotiation memos: PENDING first fragility cluster identified
