---
title: EVEZ OpenClaw
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: true
license: mit
short_description: CLAW GOBLIN — Multi-model AI gateway (Groq + OpenRouter)
---

# ⚡ EVEZ OpenClaw — CLAW GOBLIN MODE

Multi-model AI gateway with 10+ models across Groq and OpenRouter.

## Setup
Set these secrets in Space settings:
- `GROQ_API_KEY` — Groq API key (fast tier: Llama, DeepSeek)  
- `OPENROUTER_API_KEY` — OpenRouter key (smart tier: DeepSeek R1, Claude, GPT-4o)

## Models
- **evez-fast** — Llama-3.3-70B (Groq, ~50ms)
- **evez-smart** — DeepSeek R1 (OpenRouter)
- **evez-goblin** — Full CLAW GOBLIN mode
- **evez-code** — DeepSeek-R1-70B distill
- **evez-claude** — Claude 3.5 Sonnet
- **evez-flash** — Gemini Flash 1.5
