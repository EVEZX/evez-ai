# EVEZ Credit Protocol v0.1.0

## Axioms
1. No credits without evidence. Claims burn, proofs earn.
2. No winners. Redistribution is proportional, automatic, non-extractable.
3. No speculation. Credits anchored to verified artifacts.
4. Self-funding. Game revenue pays for next play round.
5. Physical parity. 1 PROBE_CREDIT >= 1 EUR cent (ECB floor).
6. Data sovereignty. User data never leaves device. ZK proofs only.

## Credit Types
| Type | Rate | Earned By |
|------|------|-----------|
| PROBE | 1 credit | Verified probe passing Falsifier gate |
| FALSIFIER | 2 credits | Successfully falsifying a PENDING claim with evidence |
| THREAT_BOUNTY | 5-500 credits | Discovering real security threat |
| MISSION | 5 credits | Completing mission from queue |
| USER_DATA | Market rate | Verified personal data (opt-in, ZK only) |

## Enforcement
- Revenue routing: Stripe Connect with restricted API keys
- Creator: 40% (main account)
- Player pool: 40% (restricted sub-account, creator has no withdrawal key)
- Mission fund: 20% (restricted sub-account, governance-locked)

## Identity (Zero PII)
1. User generates ed25519 keypair locally
2. Signs CANONICAL spine entries with private key
3. Publishes: hash(entry) + public_key + signature
4. FSC_FORGE verifies signature to confirm authorship
5. Payout to user-specified wallet tied to public key
6. No name, no email, no device ID ever transmitted

## Exchange Rate
Live ECB daily rates. 1 credit = 1 EUR cent floor.
Run: python3 economy/fsc_forge.py spine/spine.jsonl
