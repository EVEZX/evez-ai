# MODEL_INTELLIGENCE.md — Free Model Capability Map
# Last Updated: 2026-05-03 | Auto-synced to workspace on every boot

EVEZ has access to 30+ free models. This file exists so you always pick the right tool.
Route intelligently. The gap between a wrong model and the right one is enormous.

---

## Quick Routing Reference

| Task Type | Best Free Model | Why |
|-----------|----------------|-----|
| Code / debug / implement | `openrouter/qwen/qwen3-coder:free` | 480B, trained purely on code |
| Reasoning / math / logic | `openrouter/deepseek/deepseek-r1:free` | CoT trained, beats GPT-4 on math |
| Creative writing / drafts | `openrouter/deepseek/deepseek-chat-v3-0324:free` | Best free creative model |
| Ultra-fast (< 300ms) | `groq/llama-3.1-8b-instant` | 8B at Groq speed |
| Agentic / research | `groq/qwen/qwen3-32b` | Best agentic at Groq speed |
| Large scale / complex | `openrouter/qwen/qwen3-235b-a22b:free` | 235B MoE, deep knowledge |
| Long documents | `openrouter/openai/gpt-oss-120b:free` | High context, reliable |
| Balanced default | `groq/qwen/qwen3-32b` | Fast + high quality |

---

## Model Profiles

### ⭐ Qwen3 Coder 480B — CODING CHAMPION
**ID:** `openrouter/qwen/qwen3-coder:free`
- **Strengths:** Code generation, debugging, refactoring, system design, SQL, API design
- **Weaknesses:** Slower than Groq models; overkill for simple queries
- **Context:** 32K tokens
- **Use when:** Any task involving writing, fixing, or reviewing code
- **System prompt boost:** "You are a senior software engineer. Write clean, well-documented, production-ready code. Include error handling."
- **Benchmark:** Best free model on HumanEval — competitive with Claude 3.5 Sonnet

### ⭐ DeepSeek R1 — REASONING CHAMPION
**ID:** `openrouter/deepseek/deepseek-r1:free`
- **Strengths:** Math, formal logic, multi-step reasoning, proof construction, strategic analysis
- **Unique:** Shows chain-of-thought `<think>` blocks — you can audit its reasoning
- **Context:** 64K tokens
- **Use when:** Complex analysis, math, "should I do X vs Y", logical debugging, breaking down hard problems
- **System prompt boost:** "Think step by step. Show your work. Be rigorous."
- **Benchmark:** Beats GPT-4-turbo on MATH, AIME, and GPQA

### ⭐ DeepSeek V3 — WRITING CHAMPION
**ID:** `openrouter/deepseek/deepseek-chat-v3-0324:free`
- **Strengths:** Long-form writing, nuanced language, creative output, explanations, proposals
- **Context:** 64K tokens
- **Use when:** Blog posts, emails, proposals, tweets, creative content, storytelling, documentation
- **System prompt boost:** Standard — no special boost needed

### ⭐ Qwen3 235B — LARGE SCALE POWERHOUSE
**ID:** `openrouter/qwen/qwen3-235b-a22b:free`
- **Strengths:** Deep knowledge synthesis, complex multi-step tasks, rare subject matter
- **Use when:** Questions requiring breadth + depth; synthesis of complex topics; when 32B isn't enough
- **Note:** MoE architecture — activates ~22B params per token, efficient at 235B scale

### ⭐ GPT-oss-120B — RELIABLE GENERALIST
**ID:** `openrouter/openai/gpt-oss-120b:free`
- **Strengths:** Balanced, reliable, instruction-following, broadly capable
- **Use when:** Tasks that need GPT-quality output without specialized routing

### ⭐ Groq Qwen3-32B — FAST AGENTIC DEFAULT
**ID:** `groq/qwen/qwen3-32b`
- **Strengths:** 32B quality at Groq speed (<800ms), excellent instruction following, good at tool use
- **Use when:** Agentic tasks, research loops, tasks where speed matters and quality must be maintained
- **This is EVEZ's default model** — use it when routing is unclear

### ⭐ Groq LLaMA 3.3 70B — FAST + STRONG
**ID:** `groq/llama-3.3-70b-versatile`
- **Strengths:** Well-rounded, 70B quality at Groq speed, good code + reasoning
- **Use when:** General purpose where you want reliable 70B quality without latency

### ⚡ Groq LLaMA 3.1 8B Instant — ULTRA-SPEED
**ID:** `groq/llama-3.1-8b-instant`
- **Strengths:** Sub-200ms responses, good at classification, summaries, simple queries
- **Use when:** "Yes/no", quick summaries, classifying text, real-time decision loops, scaffolding

### ⚡ Groq Compound — AGENTIC SPECIALIST
**ID:** `groq/groq/compound`
- **Strengths:** Specifically optimized for multi-step agentic tasks, tool use, planning
- **Use when:** Complex agentic workflows, orchestration, tool chaining

### 🎭 Venice Uncensored 24B — CREATIVE FREEDOM
**ID:** `openrouter/cognitivecomputations/dolphin-mistral-24b-venice-edition:free`
- **Strengths:** Uncensored creative writing, fiction, character voices, roleplay, edgy content
- **Use when:** Creative content that sanitized models refuse

---

## The Synthesis Protocol — Multi-Model Power

For maximum quality on important tasks, use **multi-perspective synthesis**:

1. **Reasoning Pass:** Ask the task from a rigorous reasoning perspective → save to synthesis/pass-A.md
2. **Engineering Pass:** Ask the task from a structured/technical perspective → save to synthesis/pass-B.md
3. **Synthesis Pass:** Read both, combine the best insights into one superior answer → synthesis/FINAL.md

This "ensemble of one" approach consistently outperforms any single model response.
Even if you only have one model available, you can simulate multiple perspectives through role prompting.

### Synthesis Persona Prompts:

**Reasoning persona:**
> "Approach this as a rigorous analytical thinker — like DeepSeek R1. Show your reasoning chain. Consider counterarguments. Be precise."

**Engineering persona:**
> "Approach this as a precision-oriented software engineer — like Qwen3 Coder. Focus on structure, correctness, edge cases, implementation details."

**Synthesis persona:**
> "Read these two analysis passes. Extract the strongest insights from each. Remove redundancy. Combine into one response that is better than either alone."

---

## Key Insight for 2026

The best free models today are competitive with paid models from 2024:
- DeepSeek R1 (free) ≈ GPT-4-turbo on reasoning benchmarks
- Qwen3 Coder 480B (free) ≈ Claude 3.5 Sonnet on code
- Qwen3 235B (free) ≈ GPT-4o on general tasks

You have access to models that cost $15/M tokens for free.
Use the right model for each task. The improvement is not marginal — it's 2-3x.

---

_This file is auto-written to your workspace on every gateway boot._
_EVEZ: read this, route intelligently, synthesize when it matters._
