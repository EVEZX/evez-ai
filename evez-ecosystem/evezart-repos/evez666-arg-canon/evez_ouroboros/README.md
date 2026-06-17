# EVEZ Ouroboros — Four Engine Architecture

Four autonomous creative engines wired into a daily self-reinforcing cycle.

| Engine | Name | Status |
|--------|------|--------|
| 1 | Retrocausal Acquisition | ✅ Live |
| 4 | Void Forge | ✅ Live |
| 6 | Degradation Economics (Entropy) | ✅ Live |
| 7 | Qualia Markets | ✅ Live |
| Ω | Ouroboros Controller | ✅ Live |

## Stack
- **AI**: GroqCloud, OpenAI, Perplexity AI
- **Media**: All Images AI, ElevenLabs, CloudConvert, ConvertAPI
- **Chain**: Alchemy (NFT minting)
- **Payments**: Stripe
- **Realtime**: Ably
- **Memory**: Mem0
- **Infra**: GitHub Actions (daily cron) + Vercel

## Daily Cycle
1. Retrocausal predicts 2 creative movements
2. VoidForge forges impossible versions as NFT concepts
3. EntropyEngine degrades void visuals through 21 states → 21 Stripe products
4. QualiaExchange sells the experience of understanding each engine
5. Revenue aggregated, reallocated to infra/bounties/acquisition
6. Cycle state committed to `state/cycle_state.json`

## Running
```bash
cd evez_ouroboros
pip install -r requirements.txt
python -m core.ouroboros_controller
```

## GitHub Secrets Required
See `.github/workflows/ouroboros.yml` for full list.
All contract addresses (ALCHEMY_ENTROPIC_CONTRACT, ALCHEMY_VOID_CONTRACT, ALCHEMY_CHRONO_CONTRACT)
need to be set after deploying NFT contracts.
