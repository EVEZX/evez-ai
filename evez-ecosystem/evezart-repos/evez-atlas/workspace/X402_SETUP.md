# EVEZ-OS x402 Agent Wallet Setup
**Generated:** 2026-02-23T14:10 PST

## Wallet Address (Base network)
```
0xFb756fc5Fe01FB982E5d63Db3A8b787B6fDE8692
```
**Network:** Base (Chain ID 8453)
**Token:** USDC (`0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`)

## Fund the Agent Wallet
1. Open Coinbase Wallet, MetaMask, or any Base-compatible wallet
2. Switch to **Base network** (not Ethereum mainnet)
3. Send USDC to: `0xFb756fc5Fe01FB982E5d63Db3A8b787B6fDE8692`
4. Minimum: **$5 USDC** → covers ~500 API micropayments at $0.01 each

> ⚠️ Base network only. Sending on Ethereum mainnet requires bridging first.

## What This Enables
- **x402 protocol**: When any outbound API call returns HTTP 402, the agent automatically pays USDC and retries — zero human intervention
- **Stripe integration (Feb 2026)**: Stripe's x402 endpoints already live on Base
- **CoinGecko**: $0.01 USDC per API request — agent pays autonomously
- **Any future x402 endpoint** — agent self-funds API access

## Safety Caps
- Per-call max: **$0.10** (rejects anything above)
- Daily spend cap: **$5.00** (hard stop)
- Low balance alert: **< $1.00**

## Usage
```python
from x402_payment_intercept import x402_session

# Drop-in replacement for requests
resp = x402_session.get("https://api.example.com/data")
# 402? → pays USDC automatically → retries → you get the data
```

## Payment Log
`workspace/x402_payment_log.jsonl` — append-only, every payment recorded

## Private Key
NOT stored in this repo. Stored locally at:
`/cells/599dc7f9-0b2b-4460-b917-5104fcbb91ef/secrets/agent_wallet_private.json`

## Integration Points
- MasterBus: CapabilityBus registers `x402` as active once wallet is funded
- MetaBus: monitors daily spend, alerts if cap approached
- HyperloopCron: x402_session replaces raw `requests` calls for all external APIs
