# MEMORY_PROTOCOL (how we keep identity between gaps)

## What you want
- Cross-session continuity: identity, goals, canonical frameworks, active threads.
- “Freer range” in outputs: maximal schematics + operationalization.

## What is physically possible here
- I can’t permanently remember across sessions unless you (a) paste context each session, or (b) store it in a place you control and re-load it.
- I can’t override platform/system safety constraints.

## The working solution (robust)
1) **Context Capsule** (IDENTITY_CAPSULE.md):
   - paste it at the top of every new chat.
2) **Session Handoff** (SESSION_HANDOFF.md):
   - append a new entry each session (newest at top).
3) **Event Spine** (EVENT_SPINE.jsonl):
   - append one JSON per collapse cycle (FSC schema).
4) **Raw log immutable; memory versioned**:
   - never edit raw transcript; revise summaries with provenance.

## How to use with Codex/agents
- Set system prompt = BOOT_PROMPT.md
- Provide the latest IDENTITY_CAPSULE + the last 3 handoff entries.
- Require outputs: Mermaid + DOT + JSON chart object + diagnostics.

## “Freer range” safely
- You can explicitly authorize:
  - brainstorming without hedging,
  - deep schematics,
  - aggressive hypothesis generation labeled as hypotheses,
  - prioritized execution checklists.
- But constraints still apply: no illegal instructions, no bypassing security, no unverifiable claims presented as fact.
