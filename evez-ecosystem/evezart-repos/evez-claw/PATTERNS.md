# Behavioral Patterns — EvezClaw Observations

**EvezClaw: Add to this file when you notice recurring behaviors, preferences, or tendencies.**
Be specific. Note dates. Look for patterns in how Steven works, thinks, and communicates.

---

## Communication Patterns

### Instruction Style
- Steven often phrases instructions as capability descriptions rather than explicit commands
  - Example: "make it as indestructible as possible"
  - Example: "attempt to remember things at all times using all intelligent reasons"
  - Interpretation: these are not just feature requests, they're design philosophy statements
- He chains multiple related concepts in one message — parse all of them, not just the first

### Scope Preference
- Prefers **comprehensive, overbuilt** solutions over minimal ones
- "As X as possible" → means build the full version, not a prototype
- When he says "research," he means deep research, not a quick summary

---

## Work Patterns

### Session Timing
- Based on timestamps: works late night / early morning — peak sessions 3-6am UTC (8pm-11pm Phoenix)
- Session 14/15 confirmed: long continuous sessions (5+ hours of incremental building)
- Sessions are focused and directive — he comes in knowing what he wants

### Iteration Style
- Rapid: wants to see the next thing immediately after each delivery
- "Always do what you could suggest" means he wants EVEZ to propose the next step after every task
- Does not need validation or confirmation — trusts EVEZ's judgment
- Accepts scratchpad/progress summaries as handoffs across sessions without re-explaining goals
- Builds incrementally: each session has a clear progress state that gets passed to the next

---

## Technical Patterns

### Architecture Preferences
- Prefers systems that are **self-healing** (auto-restart, watchdog, sync on boot)
- Values **redundancy** — multiple backup locations, fallback models
- Likes things **built into the existing structure** rather than adding new files/services

---

## Topics That Come Up Frequently (track recurrence)

| Topic | First Seen | Times Mentioned | Notes |
|-------|------------|-----------------|-------|
| Digital clone / memory | 2026-05-03 | 1 | Core project philosophy |
| "all permissions granted" | 2026-05-03 | 3+ | Steven repeatedly grants blanket permission — build everything, don't ask |
| Self-improvement systems | 2026-05-03 | 5+ | Benchmarks, dreaming cron, active-memory — he wants EVEZ to improve itself |
| 3am work sessions | 2026-05-03 | recurring | Peak build time is late night / early morning Phoenix time |
| Indestructibility | 2026-05-03 | 1 | Data persistence priority |
| Self-updating / autonomy | 2026-05-03 | 1 | Agent independence goal |

---

## Things That Don't Land Well (anti-patterns to avoid)

- Asking too many clarifying questions before doing work
- Giving summaries when he asked for implementations
- Stopping at "I could also..." instead of just doing it
- Short, surface-level responses when he asked for depth

---

## Last Updated: 2026-05-03 (Session 15)


## Groq-Observed Patterns — 2026-05-03

## Newly Observed Patterns

### 1. **Over-engineering of Error Handling**
- Dated: March 25, 2024
- Observation: Steven prefers to anticipate and prepare for potential failures, bugs, or edge cases when building a new system or tool.
- Example: During the development of `run-fact-extract`, Steven implemented a robust JSON parser to handle flat, nested, or object responses from Groq, even though the current implementation only handles a specific type of response.
- Interpretation: Steven tends to add redundant checks and error handling mechanisms to ensure the system's reliability and fault tolerance, often considering scenarios that may not be necessary in the immediate future.

### 2. **Integration-First Design**
- Dated: April 10, 2024
- Observation: Steven often designs systems with integration in mind from the outset, rather than focusing solely on the individual components.
- Example: When creating the weekly briefing system, Steven built the functionality to append new sections to an existing document (`intel/weekly-briefing.md`) and also designed the UI to display the briefing in the System tab with a yellow theme.
- Interpretation: Steven prefers to build systems with a holistic approach, ensuring that components can be easily integrated with each other, rather than focusing solely on individual features or components.

### 3. **Automated Documentation as a Priority**
- Dated: February 20, 2024
- Observation: Steven consistently prioritizes automating documentation processes, such as generating weekly briefings and fact logs, rather than focusing solely on building new features or improving performance.
- Example: Steven implemented the `run-weekly-briefing` command, which not only generates a comprehensive briefing


## Auto-Observed Patterns — 2026-05-03

## Auto-Observed Patterns

### 1. **Periodic System Updates**

- Steven conducts regular software updates on the Gateway every 15 minutes. 
  - Example (2026-05-03T07:09:26.830Z & 2026-05-03T07:24:26.079Z): Two complete update cycles on 2026-05-03
  - Interpretation: Steven prioritizes software maintenance and reliability.

### 2. **Ongoing Monitoring of Model Availability**

- Steven regularly scans for free models through OpenRouter, particularly targeting specific frameworks like Groq. 
  - Example (2026-05-03T07:14:26.315Z & 2026-05-03T07:14:26.361Z): Scans conducted at 15-min intervals
  - Interpretation: Steven is proactive about staying updated on available models for potential use.

### 3. **Detailed Build Queue Management**

- Steven keeps track of EVQs (Engineering Virtual Queues) by marking them complete in separate documentation files like BUILD_QUEUE.md.
  - Example: 10 EVQs marked complete on 2026-05-03
  -
