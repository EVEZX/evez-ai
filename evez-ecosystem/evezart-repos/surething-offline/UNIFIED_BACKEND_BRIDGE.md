# Unified Backend Bridge

Status: active
Date: 2026-03-19

## Production source of truth
- Deployed backend: evez-operator on Vercel
- Repository: EvezArt/surething-offline
- Orchestration: n8n
- Audit truth: EvezArt/evez-autonomous-ledger
- Runtime agents: EvezArt/evez-agentnet

## Rule
All UI surfaces must read from one deployed backend origin. No UI surface is allowed to invent finance, workflow, ledger, or settlement state.

## Required live endpoints
- /deploy/status
- /spine/events
- /spine/verify
- /contradictions
- /canonicalize
- /fire/anchor

## Planned expansion endpoints
- /api/wallet/treasury
- /api/wallet/balances
- /api/settlements
- /api/ledger
- /api/workflows/health
- /api/agent-run
- /api/chat

## Surface wiring
- Lovable: client only, pointed at deployed backend
- Base44: client only, pointed at deployed backend
- Manus: presentation/client only, pointed at deployed backend
- n8n: trigger and orchestration layer pointed at deployed backend

## Failure policy
If live data is unavailable, surfaces must show Not connected. No simulated revenue, balances, payouts, or workflow health.

## Current deployment fact
The Vercel project evez-operator is live and READY from EvezArt/surething-offline.
