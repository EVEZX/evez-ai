# SentientPay Integration - Loop 29
Added: 2026-02-27T01:19Z

## What
Masked.cash collateral-based virtual card issuance via Solana USDC.
EVEZ earns -> USDC -> posts collateral -> issues card -> pays infra bills -> repays -> collateral back.
Closes the autonomous spending loop. No human in the loop.

## API (base: https://api.masked.cash)
- GET /api/v1/cards/available (no auth) - list templates
- GET /api/v1/cards/issue/unsigned?template_id=X&solana_payer=Y (x-api-key) - unsigned tx
- POST /api/v1/cards/issue (x-api-key + X-Transaction-Signature) - issue card

## Card Templates (live, 2026-02-27)
- Test: $5 credit limit, $1 USDC collateral
- Test2: $20 credit limit, $1 USDC collateral
- test3: $0.10 credit limit, $0.10 USDC collateral

## Required Env Vars (BLOCKED - needs Steven)
- SENTIENTPAY_API_KEY: sign up at masked.cash
- SOLANA_PRIVATE_KEY: base58 encoded private key
- SOLANA_RPC_URL: default https://api.mainnet-beta.solana.com

## Loop 29 Schedule
Weekly Monday 12pm MT. Checks SELF_NEEDS.md for billing gaps.
If gap found + keys present: issues card autonomously, logs result.
If keys missing: logs BLOCKED to SELF_NEEDS.md.

topology decides. watching it build.