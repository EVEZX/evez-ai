# EVEZ Development Circuit
## Full autonomous development loop — everywhere the bus agents can deploy

**Updated**: 2026-03-12T00:28Z  
**OpenAI Dev Assistant**: `asst_lyxTcUn0Bv2t7F6aJepN2ULT`

---

## The Circuit (5 stations)

```
[THINK]    →  [WRITE]    →  [TEST]     →  [DEPLOY]   →  [WITNESS]
Groq/OpenAI   GitHub        Vercel         Vercel prod    Spine event
Code gen      File commit   Preview+CI     Railway push   Airtable log
Context:      Auto-PR       Pass/fail      Docker Hub     GDrive mirror
Airtable      branch tag    hash           env secrets    YouTube video
```

## Quick Start

```bash
# Run a single task via Groq
python dev_circuit/circuit_runner.py --task DCT-001

# Run all tasks
python dev_circuit/circuit_runner.py --all

# Via GitHub Actions (no local setup needed)
# Go to: EvezArt/surething-offline → Actions → EVEZ Development Circuit → Run workflow

# Use OpenAI Dev Assistant for complex tasks
python dev_circuit/openai_dev_assistant.py --run "Build X that does Y"
```

## Depot Nodes (all active)

| Node | What | Status |
|------|------|--------|
| THINK-G | Groq llama-3.3-70b | ✅ < 2s latency |
| THINK-O | OpenAI gpt-4o (asst_lyxTcUn0Bv2t7F6aJepN2ULT) | ✅ code_interpreter |
| WRITE | GitHub @EvezArt | ✅ auto-commit |
| TEST | Vercel preview + GH Actions | ✅ auto-trigger |
| DEPLOY-V | Vercel | ✅ live |
| DEPLOY-R | Railway | 🔴 needs `railway up` |
| DEPLOY-D | Docker Hub | ✅ connected |
| WITNESS-S | Spine (evez-operator.vercel.app) | ✅ live |
| WITNESS-A | Airtable DEV_CIRCUIT_TASKS | ✅ active |
| WITNESS-G | Google Drive | ✅ active |
| WITNESS-Y | YouTube @lordevez | ✅ active |
| VOICE | ElevenLabs | ✅ active |
| SEARCH | Perplexity AI | ✅ active |
| MEMORY | Mem0 | ✅ active |
| VISION | Google Cloud Vision | ✅ active |

## Secrets Required (GitHub repo settings)

```
GROQ_API_KEY         → Atlas tier 2 (llama-3.3-70b)
OPENAI_API_KEY       → gpt-4o access
AIRTABLE_API_KEY     → DEV_CIRCUIT_TASKS registry
AIRTABLE_BASE_ID     → your Airtable base
BACKENDLESS_APP_ID   → spine mirror
BACKENDLESS_API_KEY  → spine mirror
YOUTUBE_CLIENT_ID    → @lordevez uploads
ELEVENLABS_API_KEY   → voice announcements
```

## Current Generated Files (DCT-001 to DCT-003)

| Task | File | Status |
|------|------|--------|
| DCT-001 | api/health.py | pending commit |
| DCT-002 | dev_circuit/hyperloop_tick.py | ✅ committed |
| DCT-003 | dev_circuit/backendless_mirror.py | ✅ committed |
| DCT-004 | dev_circuit/airtable_poller.py | scheduled |
| DCT-005 | dev_circuit/voice_announcer.py | scheduled |

## Peace Charter Compliance

- All generated code tagged with `# EVEZ-GENERATED` + evidence_hash
- Every deploy emits spine event before executing
- Circuit breaker: 3 consecutive failures → pause circuit
- Human halt: Steven can stop any station via Airtable status update
