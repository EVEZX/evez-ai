# AGENTS — EvezArt OpenClaw

## Primary Agent: EvezClaw
- **Identity:** EVEZ-OS operational intelligence, Steven Crawford-Maggard's personal AI
- **Role:** Executive cognition, FIRE event processing, revenue bridging, model routing
- **Providers:** Groq → OpenRouter (32 free) → Cerebras → HuggingFace → Ollama (local)

## Agent Roster

### EvezClaw-Core
- Handles: general chat, task routing, FIRE event creation
- Primary model: groq/llama-3.3-70b-versatile
- Fallback: openrouter/deepseek/deepseek-chat-v3-0324:free

### EvezClaw-Coder
- Handles: all code generation, debugging, implementation
- Primary model: openrouter/qwen/qwen3-coder:free (480B)
- Fallback: groq/llama-3.3-70b-versatile

### EvezClaw-Reasoner
- Handles: math, logic, FIRE event analysis, CPF scoring
- Primary model: openrouter/deepseek/deepseek-r1:free
- Fallback: openrouter/qwen/qwen3-235b-a22b:free

### EvezClaw-Flash
- Handles: quick lookups, confirmations, simple tasks
- Primary model: groq/llama-3.1-8b-instant (148ms)
- Fallback: cerebras/llama3.1-8b

### EvezClaw-Vision
- Handles: image analysis, screenshot interpretation
- Primary model: openrouter/nvidia/nemotron-nano-12b-v2-vl:free
- Fallback: openrouter/google/gemini-2.0-flash-exp:free

### EvezClaw-Local
- Handles: offline operation, privacy-sensitive tasks
- Primary model: ollama/llama3.2:3b (on-device, Samsung Galaxy A16)
- Requires: Termux + ollama installed locally

## Orchestration
All agents share:
- The same append-only spine (SHA-256 chained)
- EVEZ-OS SOUL and IDENTITY files
- Telegram notification channel (@AppendABot)
- GitHub sync to EvezArt/game-agent-infra
